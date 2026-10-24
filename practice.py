cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE 'lifespan|start_model_worker|install_cta|register_cta|run_module|pipeline_task|engine_queue' \
  artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_router.py \
  | head -50
