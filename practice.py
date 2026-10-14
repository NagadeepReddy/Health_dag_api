python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")

current = p.read_text()
changed = "scores = ops.where(positions < valid, negative, scores)"
original = "scores = ops.where(positions >= valid, negative, scores)"

assert current.count(changed) == 1, \
    "STOP: current MAX mask differs; no changes made"

backups = sorted(p.parent.glob(p.name + ".before_direction_fix_*.bak"))

matches = [
    b for b in backups
    if b.read_text() == current.replace(changed, original, 1)
]

assert matches, "STOP: matching verified backup not found; no changes made"

backup = matches[-1]
ast.parse(backup.read_text())

shutil.copy2(backup, p)

assert p.read_bytes() == backup.read_bytes()

print("PREVIOUS MAX MASK RESTORED")
print("Python syntax: PASS")
print("Original DS code: UNCHANGED")
print("Restored from:", backup)
PY
