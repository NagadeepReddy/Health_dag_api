python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max_branch_diag.py")

old = "+ [TensorType(DType.int64, [1], device=device)])"
new = "+ [TensorType(DType.int64, [1], device=device) for _ in range(2)])"

code = p.read_text()

if code.count(old) != 1:
    raise SystemExit("STOP: Expected pattern not found exactly once. No changes made.")

updated = code.replace(old, new, 1)
ast.parse(updated)

backup = p.with_suffix(".py.before_72_input_fix.bak")
shutil.copy2(p, backup)
p.write_text(updated)

print("DIAGNOSTIC GRAPH FIX: APPLIED")
print("Added missing Sibling valid-length input")
print("Python syntax: PASS")
print("Backup:", backup)
print("Original DS files: UNCHANGED")
PY
