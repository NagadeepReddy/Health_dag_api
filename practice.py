cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 3 'cta_adapter|_cta_adapter|select_scheduler' \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py
