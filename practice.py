podman run --rm --pull=never \
  -p 127.0.0.1:8000:8000 \
  -v "$PWD:/work:ro" \
  -w /work \
  --entrypoint python3 \
  cta-max-faiss:local \
  -m uvicorn cta_max.serve_max:app \
  --app-dir artifacts/v1.168-max \
  --host 0.0.0.0 \
  --port 8000
