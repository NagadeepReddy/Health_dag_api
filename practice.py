grep -nE 'is_worker_healthy|response_worker|create_background_task|start_model_worker|request_queue|response_queue' \
artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py
