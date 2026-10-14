python3 - <<'PY'
from pathlib import Path
import shutil
import ast

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
backup = p.with_suffix(".before_valid_mask_fix.bak")

if not p.exists() or not backup.exists():
    raise SystemExit("STOP: Current file or backup missing")

original = backup.read_text()
current = p.read_text()

old = "scores = ops.where(positions >= valid, negative, scores)"
new = "scores = ops.where(positions < valid, negative, scores)"

if original.count(old) != 1 or current.count(new) != 1:
    raise SystemExit("STOP: Unexpected mask code; no changes made")

if current.replace(new, old, 1) != original:
    raise SystemExit("STOP: Other changes detected; no changes made")

ast.parse(original)
shutil.copy2(backup, p)

print("Previous MAX implementation RESTORED")
print("Original DS code UNCHANGED")
print("Python syntax PASS")
PY
