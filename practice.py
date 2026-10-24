cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -C 5 \
'open_channel|request_queue|response_queue|run_iteration|CTAContext|isinstance|send_result|create_cta_scheduler' \
artifacts/v1.168-max/maxserve_cta_extension/cta_router.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler_factory.py
