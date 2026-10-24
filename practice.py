cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 5 \
'SchedulerZmqConfigs|response_queue_config|EngineQueue|start_model_worker|worker_monitor|TestClient' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_native_e2e_test.py,cta_http_pipeline.py,cta_spawn_worker.py} \
| head -130
