podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import importlib, inspect

m = importlib.import_module(
    "max.entrypoints.cli.serve.serve_api_and_model_worker"
)
fn = m.serve_api_server_and_model_worker
cls = fn.__globals__["ServingTokenGeneratorSettings"]

print("=== SERVING SETTINGS CONTRACT ===")
print("SIGNATURE:", inspect.signature(cls))
print(inspect.getsource(cls)[:5000])
'
