cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

C=/application1/cta_max_native_release_candidate_20261028

echo "=== RESPONSE WORKER AND PENDING REGISTRY ==="
sed -n '1,115p' "$C/cta_http_pipeline.py"

echo "=== HTTP RESPONSE MATCHING ==="
sed -n '35,110p' "$C/cta_router.py"

echo "=== BENCHMARK CLIENT ==="
sed -n '1,35p' \
  /application1/cta_max_true_batch_dev_20261028/cta_native_benchmark_helper.py

echo "READ-ONLY CHECK COMPLETE"
