python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
backup = p.with_suffix(".py.before_mask_direction_fix.bak")

assert backup.is_file(), "STOP: original backup missing"

current = p.read_text()
original = backup.read_text()

old = "scores = ops.where(positions >= valid, negative, scores)"
new = "scores = ops.where(positions < valid, negative, scores)"

assert original.count(old) == 1, "STOP: backup differs"
assert current.count(new) == 1, "STOP: current mask differs"
assert current.replace(new, old, 1) == original, (
    "STOP: other changes detected; no restoration"
)

ast.parse(original)
p.write_text(original)

print("Previous MAX mask RESTORED")
print("Python syntax PASS")
print("Original DS code UNCHANGED")
PY
