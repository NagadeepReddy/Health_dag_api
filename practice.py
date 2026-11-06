
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
IMAGE="localhost/max-shared-runtime:cpu"

test -f "$ROOT/python/max_runtime_shared/typed_queue.py"
test -f "$ROOT/python/max_runtime_shared/scheduler_hooks.py"
test -f "$ROOT/python/max_runtime_shared/router_contract.py"
test -f "$ROOT/python/max_runtime_shared/worker_lifecycle.py"

PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)

"${PODMAN[@]}" image exists "$IMAGE" || {
  echo "STOP: Shared MAX runtime image missing"
  exit 1
}

"${PODMAN[@]}" run --rm -i --pull=never --network=none \
  --memory=4g --pids-limit=256 \
  -v "$ROOT/python:/shared_runtime:ro" \
  -w /shared_runtime \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_runtime \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" -u - <<'PY'
import inspect

print("=== REAL MODULAR MAX RUNTIME COMPATIBILITY ===", flush=True)

from max.serve.scheduler.queues import SchedulerZmqConfigs
from max.serve.queue.zmq_queue import ZmqConfig
from max.pipelines.core import PipelineTask
from fastapi import FastAPI

from max_runtime_shared.typed_queue import (
    install_max_typed_response_queue,
)
from max_runtime_shared.scheduler_hooks import (
    SchedulerHooks,
    SharedSchedulerRegistry,
)
from max_runtime_shared.router_contract import (
    RouteBinding,
    register_model_routes,
)
from max_runtime_shared.worker_lifecycle import WorkerLifecycle

print("ACTUAL MAX INTERFACES: IMPORT PASS")
print("SHARED PYTHON MODULES: IMPORT PASS")
print("SCHEDULER SIGNATURE:", inspect.signature(SchedulerZmqConfigs))

# Use a disposable process-local scheduler patch.
# No trained model or application worker is loaded.
registry = SharedSchedulerRegistry()
events = []

registry.register(SchedulerHooks(
    model_key="runtime_probe",
    install_queue=lambda: (
        events.append("queue"),
        install_max_typed_response_queue(
            dict, owner="runtime_probe"
        )
    ),
    install_scheduler=lambda: events.append("scheduler"),
))

assert registry.activate("runtime_probe") is True
assert events == ["queue", "scheduler"]
print("REAL MAX QUEUE PATCH: INSTALLED")
print("SHARED SCHEDULER HOOK ORDER: PASS")

task = getattr(PipelineTask, "TEXT_GENERATION", None)

if task is None:
    candidates = list(PipelineTask)
    if not candidates:
        raise RuntimeError("No MAX pipeline tasks available")
    task = candidates[0]

configs = SchedulerZmqConfigs(task)

assert isinstance(configs.request_queue_config, ZmqConfig)
assert isinstance(configs.response_queue_config, ZmqConfig)

print("REAL MAX QUEUE CONFIGURATION: PASS")
print("MAX PIPELINE TASK:", task)

# Verify our router contract against the installed
# API framework. No HTTP server is started.
app = FastAPI()

async def probe_predict():
    return {"ok": True}

count = register_model_routes(
    app,
    [RouteBinding("/runtime-probe/predict", probe_predict)]
)

assert count == 1
assert any(
    r.path == "/runtime-probe/predict"
    and "POST" in getattr(r, "methods", set())
    for r in app.routes
)

print("REAL API ROUTE REGISTRATION: PASS")

# Verify the shared lifecycle can be imported and
# initialized in the MAX image without model code.
events = []

worker = WorkerLifecycle(
    create=lambda: events.append("create") or {},
    load=lambda instance: events.append("load"),
    attach_max=lambda instance: events.append("attach"),
)

worker.start()

assert worker.ready
assert events == ["create", "load", "attach"]

print("SHARED WORKER LIFECYCLE IN MAX IMAGE: PASS")

print("\n=== RESULT ===")
print("ACTUAL MAX RUNTIME API COMPATIBILITY: PASS")
print("DISPOSABLE CONTAINER: NO MODEL LOADED")
print("NO HTTP SERVER STARTED")
print("CTA / BPLAN / PZAAS: UNCHANGED")
print("LIVE MODEL INTEGRATION: STILL PENDING")
PY
SH
