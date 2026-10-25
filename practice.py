cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 8 -E \
'response_worker|healthy_worker|WORKER HEALTH|response_queue|put_nowait|ready' \
artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler_factory.py
