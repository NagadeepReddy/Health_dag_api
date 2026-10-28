cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE 'modelId|expThrottleLabel|os\.environ|start_model_worker|CTAFactoryWrapper' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py
