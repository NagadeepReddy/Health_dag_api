DIR=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

echo "=== SCHEDULER FACTORY ==="
nl -ba "$DIR/bplan_scheduler_factory.py" | head -110

echo "=== WORKER ADAPTER LOCATION ==="
find /application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension \
  -name 'bplan_native_worker_adapter.py' -print

echo "=== HTTP PIPELINE LIFECYCLE ==="
grep -nE '__aenter__|response_worker|_engine_queue|worker_monitor|_bplan_wait_for_healthy_worker' \
  "$DIR/bplan_http_pipeline.py"
