cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RIn \
  --exclude-dir=.git \
  --include='*.yaml' \
  --include='*.yml' \
  --include='*.json' \
  --include='*.env' \
  --include='*.sh' \
  -E 'modelId|expThrottleLabel|rt-pzaas-v1' . \
  | head -40
