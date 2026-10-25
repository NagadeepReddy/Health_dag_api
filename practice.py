cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 5 '_cta_native_pipeline\|_cta_wrapped' \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py
