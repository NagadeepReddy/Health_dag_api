
python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler_factory.py")

code = '''
from .cta_native_scheduler import CTANativeScheduler


def create_cta_scheduler(
    adapter,
    scheduler_zmq_configs,
    max_items_per_iteration=1,
):
    """Connect CTA inference to native MAX Serve worker queues."""

    request_queue, response_queue, cancel_queue = (
        scheduler_zmq_configs.model_worker_queues()
    )

    return CTANativeScheduler(
        adapter=adapter,
        request_queue=request_queue,
        response_queue=response_queue,
        cancel_queue=cancel_queue,
        max_items_per_iteration=max_items_per_iteration,
    )
'''

ast.parse(code)
with p.open("x") as f:
    f.write(code)

print("CTA NATIVE SCHEDULER FACTORY CREATED — SYNTAX PASS")
print("Existing MAX, DS and inference files unchanged")
PY
