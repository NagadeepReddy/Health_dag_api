cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -A 12 \
'def run_iteration|def create_cta_scheduler|def cta_infer|def install_cta_scheduler_hook' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_native_scheduler.py,cta_scheduler_factory.py,cta_router.py,cta_worker_registration.py}
