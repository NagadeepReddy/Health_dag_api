python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

old = "    return ModelWorker._call(*args, **kwargs)"
assert s.count(old) == 1, "Unexpected code; no changes made"
assert "_ORIGINAL_CALL" not in s, "Already modified; no changes made"

s = s.replace(
    "def cta_worker_entry",
    "from max.serve.pipelines.model_worker import ModelWorker\n"
    "_ORIGINAL_CALL = ModelWorker._call\n\n"
    "def cta_worker_entry",
    1
)
s = s.replace(old, "    return _ORIGINAL_CALL(*args, **kwargs)")

compile(s, str(p), "exec")
p.write_text(s)
print("SPAWN WRAPPER RECURSION GUARD: PASS")
PY
