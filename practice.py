python3 - <<'PY'
from pathlib import Path
import ast, shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
old = "-1.0e9, dtype=scores.dtype"
new = 'float("-inf"), dtype=scores.dtype'

s = p.read_text()
assert s.count(old) == 1, "STOP: expected exactly one mask value"
updated = s.replace(old, new, 1)
ast.parse(updated)

backup = p.with_suffix(".py.before_mask_alignment.bak")
shutil.copy2(p, backup)
p.write_text(updated)

print("MAX padding mask aligned with PyTorch")
print("Python syntax: PASS")
print("Backup:", backup)
print("Original DS code: UNCHANGED")
PY
