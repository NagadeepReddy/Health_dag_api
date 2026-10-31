BASE=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

grep -nEi 'spawn|register|worker|factory|bootstrap|scheduler' \
  "$BASE/cta_native_launcher.py" \
  "$BASE/cta_spawn_worker.py" \
  "$BASE/cta_scheduler_factory.py" | head -65
