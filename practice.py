timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c '
    echo "=== MAX PIPELINE RECEIVER LIFECYCLE ==="
    grep -nE -A 16 -B 5 \
      "class TokenGeneratorPipeline|def __aenter__|response_worker|_background_tasks" \
      /opt/venv/lib/python3.12/site-packages/max/serve/api_server.py | head -120
  '
