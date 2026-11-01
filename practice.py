DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

grep -RnE \
  --include='*.py' \
  'artifacts/v1\.168|CTA_MAX|cta_max|model_0_base\.pt|WDIR\s*=|BPLAN_BASE_PT|EXPECTED_FEATURES|graph\.output|Graph\(' \
  "$DST" | cut -c1-220 | head -90
