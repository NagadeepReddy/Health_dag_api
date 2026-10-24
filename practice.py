cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 5 \
'install_cta_scheduler_hook|create_cta_scheduler|scheduler_factory|sitecustomize|CTA_NATIVE' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_http_entry.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/bootstrap/sitecustomize.py
