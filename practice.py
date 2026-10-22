cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

grep -nE '^[[:space:]]*(from|import) (cta_|\.cta_|maxserve_cta_extension)' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_worker_registration.py,cta_scheduler_factory.py,cta_native_scheduler.py,cta_spawn_worker.py,cta_native_launcher.py}
