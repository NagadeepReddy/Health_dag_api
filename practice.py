CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension
BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== WORKING CTA HTTP PIPELINE ==="
sed -n '1,100p' "$CTA/cta_http_pipeline.py"

echo "=== BPLAN ROUTER ==="
sed -n '1,160p' "$BPLAN/bplan_native_serve_dev/bplan_router.py"
