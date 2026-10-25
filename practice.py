cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -m py_compile artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py && \
grep -n -C 4 '_cta_native_pipeline\|_cta_wrapped' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py
