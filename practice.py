podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect
from max.entrypoints.cli import serve_api_server_and_model_worker
from max.serve.pipelines.model_worker import start_model_worker
for f in (serve_api_server_and_model_worker, start_model_worker):
    print("\nFUNCTION:", f.__name__)
    print("SIGNATURE:", inspect.signature(f))
    print("\n".join(inspect.getsource(f).splitlines()[:45]))'
