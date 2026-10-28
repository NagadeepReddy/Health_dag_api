cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE -i \
'HTTP|response_queue|response queue|queue.get|recv|wait_for|timeout|join\(|status_code|response types' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
| tail -65
