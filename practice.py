cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.scheduler.queues import SchedulerZmqConfigs
from max.serve.pipelines import TokenGeneratorPipeline

print("=== MAX WORKER REQUEST MESSAGE ===", flush=True)

method = SchedulerZmqConfigs.model_worker_queues
print(inspect.getsource(method), flush=True)

print("\n=== HTTP QUEUE CREATION ===", flush=True)
print(inspect.getsource(TokenGeneratorPipeline.__init__), flush=True)

print("\nMESSAGE CONTRACT CHECK COMPLETE", flush=True)
PY
