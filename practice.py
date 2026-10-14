python3 - <<'PY'
from pathlib import Path
import ast
import shutil
from datetime import datetime

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
ds = Path("artifacts/v1.168/utils/dependency-utils/models.py")

s = p.read_text()
original = ds.read_bytes()

old = "scores = ops.where(positions >= valid, negative, scores)"
new = "scores = ops.where(positions < valid, negative, scores)"

assert "mask.lt(vl_len.unsqueeze(1))" in ds.read_text(), \
    "STOP: original PyTorch mask condition differs"
assert s.count(old) == 1, \
    f"STOP: expected one MAX condition, found {s.count(old)}"

updated = s.replace(old, new, 1)
ast.parse(updated)

backup = p.with_name(p.name + ".before_direction_fix_" +
                     datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak")
shutil.copy2(p, backup)
p.write_text(updated)

assert ds.read_bytes() == original
assert p.read_text().count(new) == 1

print("MAX MASK DIRECTION CORRECTED")
print("PyTorch condition: position < valid_length")
print("MAX condition:     position < valid_length")
print("Python syntax: PASS")
print("Original DS code: UNCHANGED")
print("Backup:", backup)
PY
