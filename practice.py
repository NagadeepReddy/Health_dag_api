podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c "grep -RnE 'retrieve_factory\(|validate_and_resolve_with_resolved_quantization_encoding\(' /opt/venv/lib/python3.12/site-packages/max/pipelines /opt/venv/lib/python3.12/site-packages/max/serve /opt/venv/lib/python3.12/site-packages/max/entrypoints --include='*.py' 2>/dev/null | head -30"
