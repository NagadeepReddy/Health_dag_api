cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -RnE -A 22 -B 5 \
'class CTASerializableOutput|SchedulerResult.create|response_queue.put_nowait' \
artifacts/v1.168-max/maxserve_cta_extension/ \
| head -110
