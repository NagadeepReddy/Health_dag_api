podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from max.serve.api_server import TokenGeneratorPipeline

EngineQueue = TokenGeneratorPipeline.__init__.__globals__["EngineQueue"]

for name in ("is_worker_healthy", "response_worker"):
    print("===", name, "===")
    print(inspect.getsource(getattr(EngineQueue, name)))
'
