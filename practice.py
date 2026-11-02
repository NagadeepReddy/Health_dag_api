CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension
BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

echo "=== WORKING CTA STARTUP ==="
sed -n '1,110p' "$CTA/cta_native_http_entry.py"

echo "=== BPLAN STARTUP ==="
sed -n '1,110p' "$BPLAN/bplan_native_launcher.py"
