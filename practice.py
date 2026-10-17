python3 - <<'PY'
from pathlib import Path
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_live_max_inference.py")
s = p.read_text()

old_import = "from max.driver import CPU, Tensor"
old_input = "Tensor.from_numpy(value)"

assert s.count(old_import) == 1, "STOP: Driver import differs"
assert s.count(old_input) == 1, "STOP: Input conversion differs"

backup = p.with_name(p.name + ".before_buffer_api")
assert not backup.exists(), "STOP: Backup already exists"

updated = s.replace(
    old_import, "from max.driver import CPU, Buffer"
).replace(
    old_input, "Buffer.from_numpy(value)"
)

compile(updated, str(p), "exec")
shutil.copy2(p, backup)
p.write_text(updated)

print("PASS: NVIDIA Buffer API adapter updated")
print("PASS: Python syntax valid")
print("PASS: Original runtime backed up")
print("DS CODE: UNCHANGED")
PY
