python3 - <<'PY'
from pathlib import Path
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_live_max_inference.py")
backup = p.with_name(p.name + ".before_buffer_api")

current = p.read_text()
original = backup.read_text()

assert "from max.driver import CPU, Tensor" in original
assert "Tensor.from_numpy(value)" in original
assert "_max_model" in original, "STOP: Cache missing from backup"

expected = original.replace(
    "from max.driver import CPU, Tensor",
    "from max.driver import CPU, Buffer"
).replace(
    "Tensor.from_numpy(value)",
    "Buffer.from_numpy(value)"
)

assert current == expected, "STOP: Other changes detected"

compile(original, str(p), "exec")

safety = p.with_name(p.name + ".before_approved_base_restore")
assert not safety.exists(), "STOP: Safety backup already exists"

shutil.copy2(p, safety)
p.write_text(original)

print("PASS: MAX Tensor API restored")
print("PASS: Persistent cache preserved")
print("PASS: Safety backup created")
print("DS CODE: UNCHANGED")
PY
