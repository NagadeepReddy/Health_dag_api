cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE 'faulthandler|dump_traceback|install_cta_spawn_entry|CTAFactoryWrapper|start_model_worker' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_http_entry.py
