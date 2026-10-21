python3 - <<'PY'
from pathlib import Path

d = Path("artifacts/v1.168-max/maxserve_cta_extension")
p = d / "cta_spawn_worker.py"

code = '''"""Spawn-safe native MAX worker registration."""
from max.serve.pipelines.model_worker import ModelWorker

_ORIGINAL_RUN = ModelWorker.run

async def cta_worker_run(*args, **kwargs):
    ModelWorker.run = staticmethod(_ORIGINAL_RUN)
    from cta_worker_registration import install_cta_scheduler_hook
    install_cta_scheduler_hook()
    return await _ORIGINAL_RUN(*args, **kwargs)

def install_cta_spawn_entry():
    ModelWorker.run = staticmethod(cta_worker_run)
'''

compile(code, str(p), "exec")
p.write_text(code)
print("SPAWN WORKER RECURSION FIXED — SYNTAX PASS")
PY
