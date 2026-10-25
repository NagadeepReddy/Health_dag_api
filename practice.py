cd /application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== MAX WORKER HEALTH CHECK ==="
grep -n -C 12 -E \
'def is_worker_healthy|worker_monitor|Worker failed' \
/tmp/cta_max_queues.py

echo "=== CTA WORKER MONITOR WIRING ==="
grep -n -C 5 -E \
'worker_monitor|response_worker|create_background_task' \
artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py
