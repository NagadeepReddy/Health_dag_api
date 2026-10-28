cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== NATIVE RESPONSE ROUTER ===" && \
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_router.py | sed -n '1,180p' && \
echo "=== NATIVE E2E TEST RESPONSE HANDLING ===" && \
grep -nE -C 5 'response|predict|timeout|status_code|post\(' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py | head -130
