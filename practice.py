cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RIn \
  --include='*.py' \
  -E 'webinteraction_name|sanity_input.json|adjusted_sanity|adjusted_input' \
  artifacts/v1.168-max \
  | head -60
