DEV=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

DEV="$DEV" python3 - <<'PY'
import os, ast
from pathlib import Path

path = Path(os.environ["DEV"]) / "bplan_spawn_worker.py"
registration = path.parent / "bplan_worker_registration.py"

assert path.is_file() and registration.is_file()

original = path.read_text()
old = """        pipeline.bplan_native_adapter = worker
        return pipeline"""

new = """        pipeline.bplan_native_adapter = worker

        from bplan_native_serve_dev.bplan_worker_registration import (
            install_bplan_scheduler_hook,
        )
        install_bplan_scheduler_hook()
        pipeline._bplan_native_pipeline = True
        return pipeline"""

assert original.count(old) == 1, "STOP: unexpected factory structure"
updated = original.replace(old, new)
ast.parse(updated)
path.write_text(updated)

assert "install_bplan_scheduler_hook()" in path.read_text()
print("BPLAN FACTORY-SCHEDULER CONNECTION: PASS")
print("BPLAN NATIVE HOOK: WIRED")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
