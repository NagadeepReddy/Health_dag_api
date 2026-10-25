cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -B 10 -A 20 -E \
"def run_iteration|NO_PROGRESS|get_nowait|Empty|BackgroundQueueDrainer" \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py
