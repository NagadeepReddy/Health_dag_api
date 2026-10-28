cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

echo "=== HTTP ROUTE: QUEUE SELECTION AND REQUEST REGISTRATION ==="
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_router.py \
  | sed -n '18,90p'

echo "=== HTTP PIPELINE: ENGINE QUEUE INITIALIZATION ==="
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
  | sed -n '35,90p'

echo "=== MAX: PENDING REQUEST REGISTRATION AND RESPONSE DISPATCH ==="
timeout 15s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=128m --pids-limit=16 \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c 'sed -n "153,173p;225,255p" /opt/venv/lib/python3.12/site-packages/max/serve/scheduler/queues.py'
