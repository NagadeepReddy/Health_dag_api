B=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev
C=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

echo "=== BPLAN WORKER STARTUP ==="
grep -nE 'start_model_worker|bplan_spawn|select_factory|retrieve_factory|install_bplan|BPlanFactoryWrapper|headless_workers' \
  "$B/bplan_native_launcher.py" "$B/bplan_worker_registration.py"

echo "=== BPLAN QUEUE WIRING ==="
grep -nE 'response_worker|engine_queue|response_queue|start_draining|run_iteration|create_bplan_scheduler' \
  "$B/bplan_http_pipeline.py" "$B/bplan_native_scheduler.py" "$B/bplan_scheduler_factory.py"

echo "=== WORKING CTA STARTUP ==="
grep -nE 'start_model_worker|headless_workers|CTAFactoryWrapper|install_cta_scheduler_hook' \
  "$C/cta_spawn_worker.py" 2>/dev/null
