cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 3 -E 'SchedulerZmqConfigs|request_queue_config|response_queue_config|ZmqConfig|def main|fastapi_app' \
artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_safe_probe.py
