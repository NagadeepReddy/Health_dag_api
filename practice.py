cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 3 \
'install_cta_spawn_entry|start_model_worker|serve_api_server_and_model_worker|uvicorn|lifespan|install_cta_scheduler_hook' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_http_entry.py
