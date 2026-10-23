cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE -A 8 \
'class CTAContext|def __init__|SchedulerResult\(|def register_cta_routes|async def cta_probe' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_context.py,cta_native_scheduler.py,cta_router.py}
