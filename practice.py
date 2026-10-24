cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 4 \
'_engine_queue|app\.state\.pipeline|CTANativeHTTPPipeline|worker_monitor|scheduler_zmq_configs' \
artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py
