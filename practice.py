DIR=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

echo "=== SCHEDULER RESPONSE ==="
nl -ba "$DIR/bplan_native_scheduler.py" | sed -n '75,130p'

echo "=== RESPONSE QUEUE ==="
nl -ba "$DIR/bplan_http_pipeline.py" | sed -n '85,125p'

echo "=== WORKER REGISTRATION ==="
nl -ba "$DIR/bplan_worker_registration.py" | sed -n '1,50p'
