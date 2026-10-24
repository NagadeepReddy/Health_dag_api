cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -Rn -C 3 'expThrottleLabel' \
  artifacts/v1.167 \
  artifacts/v1.168-max \
  | head -65
