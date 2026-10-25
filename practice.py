cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -n -A 35 -B 5 -E \
'def install_cta_scheduler_hook|def load_scheduler|def _call_|def __call__' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py
