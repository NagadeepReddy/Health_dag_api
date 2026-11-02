B=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_http_pipeline.py
C=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_http_pipeline.py

for f in "$B" "$C"; do
  echo "===== $f ====="
  grep -nE 'def __aenter__|def __aexit__|response_worker|wait_for_healthy|create_task|_engine_queue' "$f"
done
