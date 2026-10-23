cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

anchor = "        api.start_model_worker = wrapped\n"
assert s.count(anchor) == 1, "Unexpected code structure; no changes made"
assert "headless_workers.start_model_worker = wrapped" not in s, "Already patched"

addition = """
    # Headless MAX imports its own reference to start_model_worker.
    from max.entrypoints import workers as headless_workers
    if getattr(headless_workers, "start_model_worker", None) is original:
        headless_workers.start_model_worker = wrapped
"""

updated = s.replace(anchor, anchor + addition, 1)
ast.parse(updated)

backup = p.with_name("cta_spawn_worker.py.before_headless_fix")
if not backup.exists():
    backup.write_text(s)

p.write_text(updated)

print("CTA HEADLESS WORKER HOOK: FIXED")
print("SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY
