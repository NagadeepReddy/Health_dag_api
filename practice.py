CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension
BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== MAX WORKER REGISTRATION ==="
sed -n '1,180p' "$CTA/cta_worker_registration.py"

echo "=== MAX PIPELINE MODEL ==="
sed -n '1,140p' "$CTA/cta_pipeline_model.py"

echo "=== BPLAN FACTORY ==="
sed -n '1,100p' "$BPLAN/bplan_native_serve_dev/bplan_spawn_worker.py"
