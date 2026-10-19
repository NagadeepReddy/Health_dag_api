WITH vp_spend AS (
  SELECT
    vp_name AS manager_name,
    vp_email AS manager_email,
    vp_eid AS manager_eid,
    ROUND(SUM(total_spend_usd), 2) AS vp_total_spend_usd
  FROM ${table}
  WHERE
    vp_name IS NOT NULL
    AND TRIM(vp_name) != ''
    AND spend_year = EXTRACT(YEAR FROM CURRENT_DATE())
    AND spend_month = EXTRACT(MONTH FROM CURRENT_DATE())
    AND LOWER(TRIM(vz_env)) = 'prod'
  GROUP BY
    vp_name,
    vp_email,
    vp_eid
  HAVING SUM(total_spend_usd) >= ${thresholdUsd}
),
ldap_titles AS (
  SELECT
    TRIM(CAST(eid AS STRING)) AS employee_eid,
    CASE
      WHEN COUNT(DISTINCT NULLIF(TRIM(title), '')) = 1
      THEN MAX(NULLIF(TRIM(title), ''))
      ELSE NULL
    END AS manager_title
  FROM
    `${BUDGET_CONFIG.DATA_PROJECT}.${BUDGET_CONFIG.CURATED_DATASET}.Users_Ldap_hierarchy`
  GROUP BY employee_eid
)
SELECT
  v.*,
  COALESCE(l.manager_title, 'Title unavailable') AS manager_title
FROM vp_spend v
LEFT JOIN ldap_titles l
  ON TRIM(CAST(v.manager_eid AS STRING)) = l.employee_eid
ORDER BY
  vp_total_spend_usd DESC
