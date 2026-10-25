podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c 'nl -ba /opt/venv/lib/python3.12/site-packages/max/entrypoints/cli/serve_api_server_and_model_worker.py | sed -n "100,165p"'
