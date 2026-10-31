BASE=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

echo "=== RESPONSE QUEUE CONFIGURATION ==="
sed -n '48,67p' "$BASE/cta_queue_compat.py"

echo "=== SCHEDULER QUEUE HANDOFF ==="
sed -n '20,38p' "$BASE/cta_native_scheduler.py"
sed -n '112,125p' "$BASE/cta_native_scheduler.py"
