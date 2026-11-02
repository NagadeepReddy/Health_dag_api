DEV=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

DEV="$DEV" python3 - <<'PY'
import os
import ast
from pathlib import Path

dev = Path(os.environ["DEV"])
target = dev / "bplan_scheduler_factory.py"

assert (dev / "bplan_native_scheduler.py").is_file()
assert (dev / "bplan_context.py").is_file()
assert not target.exists(), "STOP: factory already exists"

code = '''"""BPLAN scheduler factory for native Modular MAX Serve."""

from .bplan_native_scheduler import BPlanNativeScheduler


def create_bplan_scheduler(
    adapter,
    scheduler_zmq_configs,
    max_items_per_iteration=1,
):
    if max_items_per_iteration != 1:
        raise ValueError("BPLAN batching not yet validated")

    request_queue, response_queue, cancel_queue = (
        scheduler_zmq_configs.model_worker_queues()
    )

    return BPlanNativeScheduler(
        adapter=adapter,
        request_queue=request_queue,
        response_queue=response_queue,
        cancel_queue=cancel_queue,
        max_items_per_iteration=1,
    )
'''

ast.parse(code)
target.write_text(code)

for name in (
    "bplan_context.py",
    "bplan_native_scheduler.py",
    "bplan_scheduler_factory.py",
):
    ast.parse((dev / name).read_text())

print("BPLAN SCHEDULER FACTORY: CREATED")
print("BPLAN SCHEDULER SYNTAX: PASS")
print("NATIVE QUEUE WIRING: PREPARED")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
