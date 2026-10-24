cd /application1/sajjna8/rt-pzaas-cta-offers-v1

sed -n '95,190p' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py

sed -n '1,160p' \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py
