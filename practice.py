podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c 'grep -RniE "custom.architectures|register_architecture" /opt/venv/lib/python3.12/site-packages/max/entrypoints /opt/venv/lib/python3.12/site-packages/max/pipelines 2>/dev/null | head -25'
