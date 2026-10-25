podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c '
echo "=== FACTORY CALLER ==="
sed -n "75,105p" /opt/venv/lib/python3.12/site-packages/max/entrypoints/cli/serve_api_server_and_model_worker.py
echo "=== FACTORY SELECTION ==="
sed -n "340,390p" /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/registry.py
'
