DEV=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

DEV="$DEV" python3 - <<'PY'
import os, ast
from pathlib import Path

dev = Path(os.environ["DEV"])
target = dev / "bplan_worker_registration.py"

assert (dev / "bplan_scheduler_factory.py").is_file()
assert (dev / "bplan_spawn_worker.py").is_file()
assert not target.exists(), "STOP: registration already exists"

code = '''"""BPLAN-only native MAX Serve scheduler registration."""

import inspect
from .bplan_scheduler_factory import create_bplan_scheduler


def install_bplan_scheduler_hook():
    from max.serve.pipelines.model_worker import ModelWorker

    worker_globals = inspect.unwrap(ModelWorker.run).__globals__
    original = worker_globals["load_scheduler"]

    if getattr(original, "_bplan_hook", False):
        return False

    def select_scheduler(
        pipeline, pipeline_config, settings, scheduler_zmq_configs
    ):
        adapter = getattr(pipeline, "bplan_native_adapter", None)

        if adapter is None:
            return original(
                pipeline, pipeline_config, settings, scheduler_zmq_configs
            )

        return create_bplan_scheduler(
            adapter=adapter,
            scheduler_zmq_configs=scheduler_zmq_configs,
            max_items_per_iteration=1,
        )

    select_scheduler._bplan_hook = True
    worker_globals["load_scheduler"] = select_scheduler
    return True
'''

ast.parse(code)
target.write_text(code)

print("BPLAN WORKER REGISTRATION: CREATED")
print("BPLAN SCHEDULER HOOK SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
