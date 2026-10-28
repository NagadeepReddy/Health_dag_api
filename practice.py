cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -A 5 -B 3 -E 'sample = Path|adjusted_sanity|sanity_input.json' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py && \
find artifacts/v1.168/samples artifacts/v1.168-max \
  -maxdepth 3 -type f \
  \( -name '*sanity*.json' -o -name '*adjust*.json' \) \
  -print 2>/dev/null
