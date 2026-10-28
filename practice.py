timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c '
    FILE=/opt/venv/lib/python3.12/site-packages/max/serve/pipelines/llm.py
    echo "=== BASE PIPELINE LIFECYCLE ==="
    nl -ba "$FILE" | sed -n "240,290p"
    echo "=== TOKEN GENERATOR LIFECYCLE ==="
    nl -ba "$FILE" | sed -n "400,455p"
  '
