podman run --rm --pull=never \
  --entrypoint python3 \
  cta-max-faiss:local \
  -c "import fastapi, uvicorn; print('FASTAPI + UVICORN: READY')"
