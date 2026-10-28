cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -Rn -C 10 -E \
'CTASerializableOutput|SchedulerResult.create|response_queue.put_nowait|class .*Output' \
artifacts/v1.168-max/maxserve_cta_extension/ \
--include='*.py'
