BASE=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

grep -nEi 'timeout|response_queue|wait_for|recv|worker_ready' \
  "$BASE/cta_queue_compat.py" \
  "$BASE/cta_native_launcher.py" \
  "$BASE/cta_native_scheduler.py" \
  "$BASE/cta_worker_adapter.py" | head -60
