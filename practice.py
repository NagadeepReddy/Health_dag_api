cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE 'retrieve_factory|model_factory|PIPELINE_REGISTRY|install_cta_spawn_entry' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py
