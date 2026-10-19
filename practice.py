SELECT
  vp_name AS manager_name,
  'VP' AS manager_title,
  vp_email AS manager_email,
  vp_eid AS manager_eid,
  ROUND(SUM(total_spend_usd), 2) AS vp_total_spend_usd
FROM ${table}
WHERE
  vp_name IS NOT NULL
  AND spend_year = EXTRACT(YEAR FROM CURRENT_DATE())
  AND spend_month = EXTRACT(MONTH FROM CURRENT_DATE())
  AND LOWER(TRIM(vz_env)) = 'prod'
GROUP BY
  vp_name,
  vp_email,
  vp_eid
HAVING
  SUM(total_spend_usd) >= ${thresholdUsd}
ORDER BY
  vp_total_spend_usd DESC
