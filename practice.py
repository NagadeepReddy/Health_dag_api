cd /application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== MAX HEALTH DECISION ==="
sed -n '95,135p' /tmp/cta_max_queues.py

echo "=== CTA HEALTH MONITOR CONNECTION ==="
grep -n -C 10 -E \
'worker_monitor|is_worker_healthy|EngineQueue|start_model_worker' \
artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py
