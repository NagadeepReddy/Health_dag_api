podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c 'grep -R -n -B 12 -A 20 --include="*.py" -E "retrieve_factory\(|def serve_api_server_and_model_worker" /opt/venv/lib/python3.12/site-packages/max/entrypoints | head -110'
