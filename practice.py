podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c "grep -nE '^(async )?def |FastAPI\\(|lifespan|ROUTES|include_router|app.state' /opt/venv/lib/python3.12/site-packages/max/serve/api_server.py"
