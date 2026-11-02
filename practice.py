B=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev
C=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

echo "=== BPLAN WORKER STARTUP ==="
nl -ba "$B/bplan_native_launcher.py" | sed -n '30,115p'

echo "=== WORKING CTA WORKER STARTUP ==="
nl -ba "$C/cta_spawn_worker.py" | sed -n '1,130p'
