
python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py")

code = '''
from .cta_scheduler_factory import create_cta_scheduler


def install_cta_scheduler_hook():
    """Install CTA scheduler selection inside the MAX worker process."""
    from max.serve.pipelines.model_worker import ModelWorker

    worker_globals = ModelWorker.run.__globals__
    original = worker_globals["load_scheduler"]

    if getattr(original, "_cta_hook", False):
        return False

    def select_scheduler(
        pipeline, pipeline_config, settings, scheduler_zmq_configs
    ):
        if not getattr(pipeline, "_cta_native_pipeline", False):
            return original(
                pipeline, pipeline_config, settings, scheduler_zmq_configs
            )

        adapter = getattr(pipeline, "cta_adapter", None)
        if adapter is None:
            raise RuntimeError("CTA pipeline adapter not registered")

        return create_cta_scheduler(
            adapter=adapter,
            scheduler_zmq_configs=scheduler_zmq_configs,
        )

    select_scheduler._cta_hook = True
    worker_globals["load_scheduler"] = select_scheduler
    return True
'''

ast.parse(code)
with p.open("x") as f:
    f.write(code)

print("CTA WORKER REGISTRATION HOOK CREATED — SYNTAX PASS")
print("Existing DS, MAX and inference files unchanged")
PY
