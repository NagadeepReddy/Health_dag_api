cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE -A 28 -B 8 \
'def run_iteration|def retrieve_item|CTA REQUEST RECEIVED|def __init__|def process|def enqueue' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler_hook.py \
2>/dev/null | head -180
