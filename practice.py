BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== BPLAN CONTEXT ==="
cat "$BPLAN/bplan_native_serve_dev/bplan_context.py"

echo "=== BPLAN SCHEDULER ==="
sed -n '1,210p' "$BPLAN/bplan_native_serve_dev/bplan_native_scheduler.py"

echo "=== BPLAN WORKER ADAPTER ==="
sed -n '1,160p' "$BPLAN/bplan_max_dev/bplan_native_worker_adapter.py"
