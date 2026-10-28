timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c '
    echo "=== TOKEN GENERATOR SOURCE ==="
    grep -RnE \
      "class TokenGeneratorPipeline|def __aenter__|response_worker\(" \
      /opt/venv/lib/python3.12/site-packages/max/serve/pipelines \
      --include="*.py" | head -65
  '
