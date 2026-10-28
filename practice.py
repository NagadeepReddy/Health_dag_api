cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== SPAWNED WORKER QUEUE CONFIGURATION ===" && \
grep -nE -C 5 \
'scheduler_zmq_configs|model_worker_queues|model_factory|start_model_worker|spawn' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py \
| head -110
