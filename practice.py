podman run -d --rm --pull=never \
  --name cta-max-serving-poc \
  -p 127.0.0.1:18080:8000 \
  -v "$PWD:/work:ro" \
  -v /vzwhome/sajjna8:/wheels:ro \
  -w /work \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/tmp/cta-deps:/work/artifacts/v1.168/core-artifact:/work/artifacts/v1.168-max:/work/artifacts/v1.168-max/cta_max \
  --entrypoint /bin/sh \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c 'python3 -m pip install --quiet --no-index --no-deps --target /tmp/cta-deps /wheels/faiss_cpu-1.15.1-*.whl && exec python3 -m uvicorn cta_max.serve_max:app --host 0.0.0.0 --port 8000'
