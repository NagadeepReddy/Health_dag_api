CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

echo "=== NATIVE SCHEDULER ==="
sed -n '1,180p' "$CTA/cta_native_scheduler.py"

echo "=== WORKER REGISTRATION ==="
sed -n '1,180p' "$CTA/cta_spawn_worker.py"

echo "=== HTTP PIPELINE ==="
sed -n '1,150p' "$CTA/cta_http_pipeline.py"
