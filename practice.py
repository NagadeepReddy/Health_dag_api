cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== ACTUAL WEIGHT FILE LOCATIONS ===" && \
find artifacts/v1.168 artifacts/v1.168-max \
  -name 'fn_norml_g.npy' -print 2>/dev/null && \
echo "=== CODE REFERENCES ===" && \
grep -RIn --include='*.py' \
  'fn_norml_g.npy' \
  artifacts/v1.168-max/cta_max \
  artifacts/v1.168/core-artifact 2>/dev/null | head -20 && \
echo "=== EXPECTED DIRECTORY ===" && \
ls -ld artifacts/v1.168-max/cta_max/sequence_weights \
  artifacts/v1.168-max/cta_max/grecbase_integration_weights 2>&1
