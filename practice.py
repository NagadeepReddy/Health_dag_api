cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.scheduler.queues import SchedulerZmqConfigs
from max.serve.api_server import TokenGeneratorPipeline

print("=== MAX WORKER REQUEST QUEUES ===")
print(inspect.getsource(SchedulerZmqConfigs.model_worker_queues))

print("\n=== MAX HTTP ENGINE QUEUE ===")
print(inspect.getsource(TokenGeneratorPipeline.__init__))

print("\nQUEUE CONTRACT CHECK COMPLETE")
PY
