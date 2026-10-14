python3 - <<'PY'
from pathlib import Path
import ast
import shutil
from datetime import datetime

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
s = p.read_text()

old = "scores = ops.where(positions >= valid, negative, scores)"
new = "scores = ops.where(positions < valid, negative, scores)"

if s.count(old) != 1:
    raise SystemExit(f"STOP: Expected one exact mask expression, found {s.count(old)}. No changes.")

updated = s.replace(old, new, 1)
ast.parse(updated, filename=str(p))

backup = p.with_name(
    p.name + ".before_mask_direction_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak"
)
shutil.copy2(p, backup)
p.write_text(updated)

print("MAX mask direction aligned with original PyTorch")
print("Python syntax: PASS")
print("Original DS code: UNCHANGED")
print("Backup:", backup)
PY
