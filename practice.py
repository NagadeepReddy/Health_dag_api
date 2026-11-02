B=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py
C=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_http_entry.py

echo "=== BPLAN STARTUP ==="
grep -nE 'factory|spawn|start_model_worker|fastapi_app|ServingTokenGeneratorSettings|uvicorn|install_' "$B"

echo "=== WORKING CTA STARTUP ==="
grep -nE 'factory|spawn|start_model_worker|fastapi_app|ServingTokenGeneratorSettings|uvicorn|install_' "$C"
