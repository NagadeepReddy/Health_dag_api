podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.api_server import TokenGeneratorPipeline
from max.interfaces.queue import BackgroundQueueDrainer

EngineQueue = TokenGeneratorPipeline.__init__.__globals__["EngineQueue"]
drain_queue = BackgroundQueueDrainer._drain_queue_background.__globals__["drain_queue"]

print("=== HTTP REQUEST SENDING ===")
print(inspect.getsource(EngineQueue.stream))

print("\n=== WORKER REQUEST RECEIVING ===")
print(inspect.getsource(drain_queue))
PY
