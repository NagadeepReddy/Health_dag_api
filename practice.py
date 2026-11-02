B=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev
C=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

echo "=== WORKING CTA RESPONSE HANDLING ==="
grep -n -C 5 -E 'SchedulerResult|RequestID|response_queue|put_nowait' "$C/cta_native_scheduler.py"

echo "=== BPLAN RESPONSE HANDLING ==="
grep -n -C 5 -E 'SchedulerResult|RequestID|response_queue|put_nowait' "$B/bplan_native_scheduler.py"
