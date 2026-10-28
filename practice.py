cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== WEIGHT REFERENCES ===" && \
grep -RInE 'fn_norml_g|sequence_weights' \
  artifacts/v1.168-max/cta_max \
  --include='*.py' 2>/dev/null | head -35; \
echo "=== EXPECTED DIRECTORY ==="; \
ls -ld artifacts/v1.168-max/cta_max/sequence_weights 2>&1; \
echo "=== EXISTING WEIGHT DIRECTORY ==="; \
ls -ld artifacts/v1.168-max/cta_max/grecbase_integration_weights 2>&1
