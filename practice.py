cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 5 -E 'response_queue|response_worker|_engine_queue|get_nowait|receive|recv' \
artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_http_entry.py
