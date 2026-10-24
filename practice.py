podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'sed -n "85,170p" /opt/venv/lib/python3.12/site-packages/max/entrypoints/cli/serve/serve_api_and_model_worker.py'
