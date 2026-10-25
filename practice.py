cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -n -C 8 -E \
'response_worker|_background_tasks|start_background|create_task|worker_monitor|response_queue' \
artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py | tail -110
