python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
backup = p.with_suffix(".py.before_branch_order_fix")

old = "(seq, context, search0, search1, jet, ihq, sibling, task)"
new = "(seq, context, search0, search1, task, jet, ihq, sibling)"

source = p.read_text()

if old not in source:
    if new in source:
        print("BRANCH ORDER ALREADY CORRECT — nothing changed")
    else:
        print("STOP: Expected branch order not found — nothing changed")
    raise SystemExit(0)

assert source.count(old) == 1, "Unexpected multiple occurrences"

updated = source.replace(old, new)
ast.parse(updated, filename=str(p))

if not backup.exists():
    shutil.copy2(p, backup)

p.write_text(updated)

print("BRANCH ORDER CORRECTED")
print("PYTHON SYNTAX: PASS")
print("BACKUP:", backup)
print("ORIGINAL PYTORCH/DS CODE UNCHANGED")
PY
