BASE=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/maxserve_cta_extension

echo "=== HTTP RESPONSE QUEUE HANDLING ==="
sed -n '1,165p' "$BASE/cta_http_pipeline.py"

echo "=== ROUTER TIMEOUT AND RESPONSE HANDLING ==="
grep -nE -C 4 'timeout|wait_for|504|response_queue|request_id' "$BASE/cta_router.py"
