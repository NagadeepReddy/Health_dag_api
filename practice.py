podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import importlib, inspect

m = importlib.import_module(
    "max.entrypoints.cli.serve.serve_api_and_model_worker"
)
src, start = inspect.getsourcelines(
    m.serve_api_server_and_model_worker
)

for i, line in enumerate(src):
    if any(x in line for x in (
        "retrieve_factory", "ServingTokenGeneratorSettings",
        "tokenizer", "model_factory"
    )):
        print(f"=== LINE {start+i} ===")
        for j in range(max(0,i-4), min(len(src),i+7)):
            print(f"{start+j}: {src[j].rstrip()}")
'
