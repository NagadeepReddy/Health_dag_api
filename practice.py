python3 - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py")
s = p.read_text()

anchor = '    print("BPLAN NATIVE MAX LAUNCHER: REGISTERED", flush=True)'
patch = '''    # Match the working CTA headless-worker startup wiring.
    from max.serve import headless_workers
    if getattr(headless_workers, "start_model_worker", None) is original_spawn:
        headless_workers.start_model_worker = bplan_spawn
    assert headless_workers.start_model_worker is bplan_spawn
    print("BPLAN HEADLESS WORKER: WIRED", flush=True)

'''

assert s.count(anchor) == 1, "STOP: launcher structure unexpected"
if "BPLAN HEADLESS WORKER: WIRED" not in s:
    updated = s.replace(anchor, patch + anchor)
    ast.parse(updated)
    backup = p.with_suffix(".py.before_headless_fix")
    if not backup.exists():
        backup.write_text(s)
    p.write_text(updated)

ast.parse(p.read_text())
print("BPLAN HEADLESS WORKER PATCH: PASS")
print("BPLAN LAUNCHER SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
