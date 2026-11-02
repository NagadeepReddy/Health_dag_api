DIR=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

echo "=== BPLAN SCHEDULER ==="
nl -ba "$DIR/bplan_native_scheduler.py" | sed -n '1,135p'

echo "=== BPLAN WORKER FACTORY ==="
nl -ba "$DIR/bplan_spawn_worker.py" | sed -n '1,100p'

echo "=== BPLAN ROUTER ==="
nl -ba "$DIR/bplan_router.py" | sed -n '14,55p'
