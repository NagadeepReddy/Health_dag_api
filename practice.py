timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c '
    echo "=== HTTP QUEUE CONFIGURATION ==="
    sed -n "35,85p" /opt/venv/lib/python3.12/site-packages/max/serve/scheduler/queues.py

    echo "=== MAX HTTP RECEIVER STARTUP ==="
    grep -n -A 55 -B 5 "async def __aenter__" \
      /opt/venv/lib/python3.12/site-packages/max/serve/api_server.py | head -95
  '
