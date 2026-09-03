/**
 * Alert #4
 *
 * Weekly use-case spend deviation monitoring.
 *
 * Flags use cases where latest completed week's spend
 * increased by more than the configured threshold
 * compared with the previous week.
 *
 * Also identifies VAST/wallet mapping issues.
 */
function getWeeklyDeviationAlerts() {
  const threshold =
    BUDGET_CONFIG.WEEKLY_DEVIATION_THRESHOLD_PCT;

  const query = `
    WITH wallet_vast_raw AS (
      SELECT DISTINCT
        SAFE_CAST(TRIM(vast_id) AS INT64) AS vast_id,
        w.wallet_id,
        w.budget
      FROM
        \`${BUDGET_CONFIG.DATA_PROJECT}.${BUDGET_CONFIG.WALLET_DATASET}.${BUDGET_CONFIG.WALLETS_TABLE}\` w,
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
        \`${BUDGET_CONFIG.DATA_PROJECT}.${BUDGET_CONFIG.CURATED_DATASET}.${BUDGET_CONFIG.APPLICATION_HIERARCHY_TABLE}\`
      WHERE
        vastapplid IS NOT NULL
        AND TRIM(vastapplid) != ''
        AND vastID IS NOT NULL
    ),

    current_month AS (
      SELECT
        COALESCE(NULLIF(TRIM(vz_usecase), ''), 'MISSING')
          AS vz_usecase,
        COALESCE(NULLIF(TRIM(vz_vsad), ''), 'MISSING')
          AS vz_vsad,
        SUM(spend_usd) AS current_month_spend_usd
      FROM
        \`${BUDGET_CONFIG.DATA_PROJECT}.${BUDGET_CONFIG.CURATED_DATASET}.${BUDGET_CONFIG.SPEND_ENRICHED_TABLE}\`
      WHERE
        spend_date >= DATE_TRUNC(CURRENT_DATE(), MONTH)
        AND spend_date <= CURRENT_DATE()
      GROUP BY
        vz_usecase,
        vz_vsad
    ),

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
        \`${BUDGET_CONFIG.DATA_PROJECT}.${BUDGET_CONFIG.CURATED_DATASET}.${BUDGET_CONFIG.SPEND_ENRICHED_TABLE}\`

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

    monthly_spend AS (
      SELECT
        DATE_TRUNC(spend_date, MONTH) AS month_start,

        COALESCE(NULLIF(TRIM(vz_usecase), ''), 'MISSING')
          AS vz_usecase,

        COALESCE(NULLIF(TRIM(vz_vsad), ''), 'MISSING')
          AS vz_vsad,

        SUM(spend_usd) AS monthly_spend_usd

      FROM
        \`${BUDGET_CONFIG.DATA_PROJECT}.${BUDGET_CONFIG.CURATED_DATASET}.${BUDGET_CONFIG.SPEND_ENRICHED_TABLE}\`

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
            ) * 100 > ${threshold}
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
      weekly_change_usd DESC
  `;

  console.log(
    'Executing Alert #4 weekly use-case deviation query...'
  );

  const results = runBigQuery(query);

  console.log(
    'Alert #4 returned rows: ' +
    results.length
  );

  console.log(
    JSON.stringify(results)
  );

  return results;
}
