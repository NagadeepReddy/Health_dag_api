python3 - <<'PY'
from pathlib import Path
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_live_max_inference.py")
s = p.read_text()

assert s.count("from max.driver import CPU, Buffer") == 1
assert s.count("Buffer.from_numpy(value)") == 1
assert "_max_model" in s, "STOP: Persistent cache missing"

backup = p.with_name(p.name + ".before_local_image_restore")
assert not backup.exists(), "STOP: Backup already exists"

updated = s.replace(
    "from max.driver import CPU, Buffer",
    "from max.driver import CPU, Tensor"
).replace(
    "Buffer.from_numpy(value)",
    "Tensor.from_numpy(value)"
)

compile(updated, str(p), "exec")
shutil.copy2(p, backup)
p.write_text(updated)

print("PASS: Compatible MAX Tensor API restored")
print("PASS: Persistent cache retained")
print("PASS: Backup created; syntax valid")
print("DS CODE: UNCHANGED")
PY
