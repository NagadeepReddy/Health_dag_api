python3 - <<'PY'
from pathlib import Path

d = Path("artifacts/v1.168-max/maxserve_cta_extension")
p = d / "cta_spawn_worker.py"

code = '''"""CTA registration inside the spawned MAX worker."""

def cta_worker_entry(*args, **kwargs):
    from cta_worker_registration import install_cta_scheduler_hook
    install_cta_scheduler_hook()

    from max.serve.pipelines.model_worker import ModelWorker
    return ModelWorker._call(*args, **kwargs)


def install_cta_spawn_entry():
    from max.serve.pipelines.model_worker import ModelWorker
    ModelWorker._call = staticmethod(cta_worker_entry)
'''

launcher = (d / "cta_native_launcher.py").read_text()
assert "install_cta_spawn_entry()" in launcher
compile(code, str(p), "exec")
p.write_text(code)

print("SPAWN-SAFE WORKER ENTRY: SYNTAX PASS")
print("LAUNCHER CONNECTION: PASS")
PY
