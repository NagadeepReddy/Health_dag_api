cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RIn \
  --include='*.py' \
  --include='*.yaml' \
  --include='*.yml' \
  --include='*.json' \
  --include='*.sh' \
  -E 'modelId|MODEL_ID' \
  artifacts/v1.168/core-artifact \
  artifacts/v1.168-max/maxserve_cta_extension \
  | head -40
