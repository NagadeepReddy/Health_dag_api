cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -RnE 'SchedulerResult|run_iteration|response_queue|send_result' \
artifacts/v1.168-max/maxserve_cta_extension/ | head -60
