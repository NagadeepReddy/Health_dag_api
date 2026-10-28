cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE 'request_id|wire_request_id|RequestID|SchedulerResult|response_queue|CTASerializableOutput' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_context.py,cta_router.py,cta_native_scheduler.py}
