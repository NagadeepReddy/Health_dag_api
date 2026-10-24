cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -RnE \
'create_cta_scheduler|CTANativeScheduler|install_cta_scheduler_hook|run_iteration' \
artifacts/v1.168-max/maxserve_cta_extension \
--include='*.py' | grep -v __pycache__
