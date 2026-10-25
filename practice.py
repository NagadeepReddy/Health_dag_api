cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -n -C 5 -E \
'response_worker|create_background_task|_background_tasks|_engine_queue|async def start|def start' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_http_pipeline.py,cta_native_live_server.py}
