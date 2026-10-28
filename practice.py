cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 8 -E \
'def .*predict|_engine_queue|503|is_worker_healthy|request_queue|response_queue|enqueue|generate' \
artifacts/v1.168-max/maxserve_cta_extension/cta_router.py
