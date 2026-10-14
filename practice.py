python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
s = p.read_text()

old = "scores = ops.where(positions >= valid, negative, scores)"
new = "scores = ops.where(positions < valid, negative, scores)"

assert s.count(old) == 1, (
    f"STOP: Expected exactly one mask expression; found {s.count(old)}. No changes."
)

updated = s.replace(old, new, 1)
ast.parse(updated)

backup = p.with_suffix(".py.before_mask_direction_fix.bak")
assert not backup.exists(), "STOP: backup already exists; no changes."

shutil.copy2(p, backup)
p.write_text(updated)

print("MAX mask direction aligned with original PyTorch")
print("Python syntax: PASS")
print("Original DS code: UNCHANGED")
print("Backup:", backup)
PY
