cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== RESPONSE QUEUE CONFIGURATION TRACE ===" && \
grep -nE 'response_queue_config|response_queue|scheduler_zmq_configs|model_worker_queues|api_worker_queues|ZmqConfig' \
  artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler_factory.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
  | head -65
