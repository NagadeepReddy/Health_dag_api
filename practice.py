cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE 'install_cta_scheduler_hook|install_cta_spawn_entry|register_cta_architecture|register_cta_routes|model-path|custom-architectures' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_native_launcher,cta_spawn_worker,cta_worker_registration}.py
