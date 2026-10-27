podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c "grep -Rn -A 85 '^class PipelineModel' /opt/venv/lib/python3.12/site-packages/max/pipelines/lib --include='*.py' 2>/dev/null | head -100"
