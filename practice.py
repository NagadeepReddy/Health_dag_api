cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 5 \
'CTA_NATIVE_FACTORY_ENTERED|CTAFactoryWrapper|def __call__|def install_cta_scheduler_hook|load_scheduler|attach_max|CTA_QUEUE_INITIALIZED' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler_hook.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py 2>/dev/null | head -130
