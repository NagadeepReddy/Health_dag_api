cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE 'start_model_worker|model_factory|CTAFactoryWrapper|install_cta_spawn_entry' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py
