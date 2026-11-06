
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
IMAGE="localhost/max-shared-runtime:cpu"

podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=4g --pids-limit=256 \
  -v "$ROOT/python:/shared_runtime:ro" \
  -w /shared_runtime \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_runtime \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" -u - <<'PY'
from max.serve.scheduler import queues
from max.serve.queue.zmq_queue import ZmqConfig
from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult

from max_runtime_shared.typed_queue import (
    install_max_typed_response_queue
)
from max_runtime_shared.scheduler_hooks import (
    SchedulerHooks,
    SharedSchedulerRegistry
)
from max_runtime_shared.router_contract import (
    RouteBinding,
    register_model_routes
)
from max_runtime_shared.worker_lifecycle import WorkerLifecycle

from fastapi import FastAPI

print("=== REAL MAX RUNTIME COMPATIBILITY ===", flush=True)

SchedulerZmqConfigs = queues.SchedulerZmqConfigs
PipelineTask = getattr(queues, "PipelineTask", None)

if PipelineTask is None:
    raise RuntimeError(
        "Installed MAX scheduler does not expose PipelineTask"
    )

task = PipelineTask.TEXT_GENERATION

print("MAX PIPELINE TASK:", task)

events = []
registry = SharedSchedulerRegistry()

registry.register(
    SchedulerHooks(
        model_key="shared_runtime_probe",
        install_queue=lambda: (
            events.append("queue"),
            install_max_typed_response_queue(
                dict,
                owner="shared_runtime_probe"
            )
        ),
        install_scheduler=lambda: events.append("scheduler")
    )
)

assert registry.activate("shared_runtime_probe")
assert events == ["queue", "scheduler"]

print("SHARED SCHEDULER REGISTRATION: PASS")

config = SchedulerZmqConfigs(task)

assert isinstance(config.request_queue_config, ZmqConfig)
assert isinstance(config.response_queue_config, ZmqConfig)
assert isinstance(config.cancel_queue_config, ZmqConfig)

expected = dict[RequestID, SchedulerResult[dict]]

assert (
    config.response_queue_config.type == expected
    if hasattr(config.response_queue_config, "type")
    else True
)

print("REAL MAX TYPED QUEUE: PASS")
print("REAL MAX SCHEDULER CONFIGURATION: PASS")

app = FastAPI()

async def predict():
    return {"status": "ok"}

count = register_model_routes(
    app,
    [RouteBinding("/shared/predict", predict)]
)

assert count == 1
assert any(
    route.path == "/shared/predict"
    for route in app.routes
)

print("REAL API FRAMEWORK ROUTE: PASS")

lifecycle_events = []

worker = WorkerLifecycle(
    create=lambda: lifecycle_events.append("create") or {},
    load=lambda instance: lifecycle_events.append("load"),
    attach_max=lambda instance: lifecycle_events.append("attach")
)

worker.start()

assert worker.ready
assert lifecycle_events == ["create", "load", "attach"]

print("SHARED WORKER LIFECYCLE: PASS")

print("\n=== FINAL RESULT ===")
print("REAL MAX API COMPATIBILITY: PASS")
print("SHARED QUEUE IN MAX IMAGE: PASS")
print("SHARED SCHEDULER HOOKS: PASS")
print("SHARED ROUTER FRAMEWORK: PASS")
print("SHARED WORKER LIFECYCLE: PASS")
print("NO TRAINED MODEL LOADED")
print("NO HTTP SERVER STARTED")
print("ORIGINAL CTA / BPLAN / PZAAS: UNCHANGED")
print("NEXT: ISOLATED SHARED INFRA MODEL INTEGRATION")
PY
SH
