cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -n -C 7 -E \
'ProcessMonitor|worker_monitor|register_process|register_worker|spawn_worker|worker_process' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_native_live_server.py,cta_spawn_worker.py,cta_http_pipeline.py} | tail -100
