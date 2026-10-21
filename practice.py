python3 - <<'PY'
from pathlib import Path

d = Path("artifacts/v1.168-max/maxserve_cta_extension")
p = d / "cta_native_launcher.py"
s = p.read_text()

old = "    install_cta_scheduler_hook()\n"
assert s.count(old) == 1, "Launcher differs; no changes made"

worker = '''"""Spawn-safe CTA worker entry point."""

def cta_worker_entry(*args, **kwargs):
    from cta_worker_registration import install_cta_scheduler_hook
    install_cta_scheduler_hook()

    from max.serve.pipelines.model_worker import ModelWorker
    return ModelWorker._call(*args, **kwargs)


def install_cta_spawn_entry():
    from max.serve.pipelines.model_worker import ModelWorker
    ModelWorker._call = staticmethod(cta_worker_entry)
'''

updated = s.replace(
    old,
    "    from cta_spawn_worker import install_cta_spawn_entry\n"
    "    install_cta_spawn_entry()\n"
)

compile(worker, str(d / "cta_spawn_worker.py"), "exec")
compile(updated, str(p), "exec")

(d / "cta_spawn_worker.py").write_text(worker)
p.write_text(updated)

print("SPAWN-SAFE CTA ENTRY: CREATED")
print("LAUNCHER UPDATED: SYNTAX PASS")
PY
