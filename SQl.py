
WITH wallet_vast_raw AS (
  SELECT DISTINCT
    SAFE_CAST(TRIM(vast_id) AS INT64) AS vast_id,
    w.wallet_id,
    w.budget
  FROM
    `vz-it-pr-k2vv-vegsdo-0.ai_platform_gateway_repl_ops_tbls.gcp_prod_k2vv_vegsdo_0_useast4_vz_ai_platform_hub_wallets` w,
    UNNEST(
      SPLIT(
        REGEXP_REPLACE(
          COALESCE(w.vast_id_mappings, ''),
          r'[{}]',
          ''
        ),
        ','
      )
    ) AS vast_id
  WHERE
    SAFE_CAST(TRIM(vast_id) AS INT64) IS NOT NULL
    AND w.budget IS NOT NULL
    AND w.budget > 0
),

/* Validated:
   duplicate wallets for a VAST ID currently have
   the same budget, so use one budget per VAST ID. */
wallet_vast AS (
  SELECT
    vast_id,
    MAX(budget) AS budget
  FROM wallet_vast_raw
  GROUP BY vast_id
),

vsad_vast_mapping AS (
  SELECT DISTINCT
    UPPER(TRIM(vastapplid)) AS vz_vsad_key,
    vastID AS vast_id
  FROM
    `vz-it-pr-k2vv-vegsdo-0.ai_platform_gateway_crtd_tbls.curated_litellm_application_hierarchy_summary`
  WHERE
    vastapplid IS NOT NULL
    AND TRIM(vastapplid) != ''
    AND vastID IS NOT NULL
),

/* Current month budget consumption */
current_month AS (
  SELECT
    COALESCE(NULLIF(TRIM(vz_usecase), ''), 'MISSING')
      AS vz_usecase,

    COALESCE(NULLIF(TRIM(vz_vsad), ''), 'MISSING')
      AS vz_vsad,

    SUM(spend_usd) AS current_month_spend_usd

  FROM
    `vz-it-pr-k2vv-vegsdo-0.ai_platform_gateway_crtd_tbls.curated_litellm_spend_enriched`

  WHERE
    spend_date >= DATE_TRUNC(CURRENT_DATE(), MONTH)
    AND spend_date <= CURRENT_DATE()

  GROUP BY
    vz_usecase,
    vz_vsad
),

/* Completed weekly spend */
weekly_spend AS (
  SELECT
    DATE_TRUNC(
      spend_date,
      WEEK(MONDAY)
    ) AS week_start,

    COALESCE(NULLIF(TRIM(vz_usecase), ''), 'MISSING')
      AS vz_usecase,

    COALESCE(NULLIF(TRIM(vz_vsad), ''), 'MISSING')
      AS vz_vsad,

    SUM(spend_usd) AS weekly_spend_usd

  FROM
    `vz-it-pr-k2vv-vegsdo-0.ai_platform_gateway_crtd_tbls.curated_litellm_spend_enriched`

  WHERE
    spend_date <
      DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))

  GROUP BY
    week_start,
    vz_usecase,
    vz_vsad
),

weekly_comparison AS (
  SELECT
    week_start,
    vz_usecase,
    vz_vsad,
    weekly_spend_usd,

    LAG(weekly_spend_usd) OVER (
      PARTITION BY
        vz_usecase,
        vz_vsad
      ORDER BY
        week_start
    ) AS previous_week_spend_usd

  FROM weekly_spend
),

latest_completed_week AS (
  SELECT MAX(week_start) AS week_start
  FROM weekly_spend
),

/* Last 4 completed weeks - context only */
weekly_average AS (
  SELECT
    vz_usecase,
    vz_vsad,
    AVG(weekly_spend_usd) AS avg_weekly_spend_usd

  FROM weekly_spend

  WHERE
    week_start >= DATE_SUB(
      DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)),
      INTERVAL 4 WEEK
    )

  GROUP BY
    vz_usecase,
    vz_vsad
),

/* Last 3 completed months - context only */
monthly_spend AS (
  SELECT
    DATE_TRUNC(spend_date, MONTH) AS month_start,

    COALESCE(NULLIF(TRIM(vz_usecase), ''), 'MISSING')
      AS vz_usecase,

    COALESCE(NULLIF(TRIM(vz_vsad), ''), 'MISSING')
      AS vz_vsad,

    SUM(spend_usd) AS monthly_spend_usd

  FROM
    `vz-it-pr-k2vv-vegsdo-0.ai_platform_gateway_crtd_tbls.curated_litellm_spend_enriched`

  WHERE
    spend_date >= DATE_SUB(
      DATE_TRUNC(CURRENT_DATE(), MONTH),
      INTERVAL 3 MONTH
    )
    AND spend_date <
      DATE_TRUNC(CURRENT_DATE(), MONTH)

  GROUP BY
    month_start,
    vz_usecase,
    vz_vsad
),

monthly_average AS (
  SELECT
    vz_usecase,
    vz_vsad,
    AVG(monthly_spend_usd) AS avg_monthly_spend_usd

  FROM monthly_spend

  GROUP BY
    vz_usecase,
    vz_vsad
),

classified AS (
  SELECT
    c.week_start,
    c.vz_usecase,
    c.vz_vsad,
    vm.vast_id,

    ROUND(w.budget, 2)
      AS mapped_budget_usd,

    ROUND(cm.current_month_spend_usd, 2)
      AS current_month_spend_usd,

    ROUND(
      SAFE_DIVIDE(
        cm.current_month_spend_usd,
        w.budget
      ) * 100,
      2
    ) AS budget_used_pct,

    ROUND(c.previous_week_spend_usd, 2)
      AS previous_week_spend_usd,

    ROUND(c.weekly_spend_usd, 2)
      AS latest_week_spend_usd,

    ROUND(
      c.weekly_spend_usd -
      c.previous_week_spend_usd,
      2
    ) AS weekly_change_usd,

    ROUND(
      SAFE_DIVIDE(
        c.weekly_spend_usd -
        c.previous_week_spend_usd,
        c.previous_week_spend_usd
      ) * 100,
      2
    ) AS weekly_deviation_pct,

    ROUND(wa.avg_weekly_spend_usd, 2)
      AS avg_weekly_spend_usd,

    ROUND(ma.avg_monthly_spend_usd, 2)
      AS avg_monthly_spend_usd,

    CASE
      WHEN vm.vast_id IS NULL
        THEN 'NO VAST ID'

      WHEN w.vast_id IS NULL
        THEN 'NO WALLET/BUDGET'

      ELSE 'MAPPED'
    END AS mapping_status,

    CASE
      WHEN vm.vast_id IS NULL
        THEN 'MAPPING ISSUE'

      WHEN w.vast_id IS NULL
        THEN 'MAPPING ISSUE'

      ELSE 'WEEKLY DEVIATION'
    END AS review_type

  FROM weekly_comparison c

  JOIN latest_completed_week l
    ON c.week_start = l.week_start

  LEFT JOIN current_month cm
    ON c.vz_usecase = cm.vz_usecase
   AND c.vz_vsad = cm.vz_vsad

  LEFT JOIN weekly_average wa
    ON c.vz_usecase = wa.vz_usecase
   AND c.vz_vsad = wa.vz_vsad

  LEFT JOIN monthly_average ma
    ON c.vz_usecase = ma.vz_usecase
   AND c.vz_vsad = ma.vz_vsad

  LEFT JOIN vsad_vast_mapping vm
    ON UPPER(TRIM(c.vz_vsad))
       = vm.vz_vsad_key

  LEFT JOIN wallet_vast w
    ON vm.vast_id = w.vast_id

  WHERE
    c.previous_week_spend_usd IS NOT NULL
    AND c.previous_week_spend_usd > 0

    AND SAFE_DIVIDE(
          c.weekly_spend_usd -
          c.previous_week_spend_usd,
          c.previous_week_spend_usd
        ) * 100 > 25
)

SELECT
  *
FROM classified

ORDER BY
  CASE
    WHEN review_type = 'WEEKLY DEVIATION'
      THEN 1
    ELSE 2
  END,
  weekly_change_usd DESC;
