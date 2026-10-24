cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE 'CTANativeHTTPPipeline|TokenGeneratorPipeline|api_server|register_cta_routes|install_cta_spawn_entry|runpy' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py
