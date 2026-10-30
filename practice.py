PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast
import shutil
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
target = base / "real_max_batch2_backend.py"
candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
)

contract = candidate / "run_batch2_contract.py"
graph = candidate / "grecbase_fusion_full_head_72_max.py"

for p in (target, contract, graph):
    if not p.is_file():
        raise SystemExit(f"STOP: Required file missing: {p}")

source = target.read_text()
marker = "# CTA_BATCH2_IMPORT_PRIORITY_FIX"

if marker in source:
    print("IMPORT FIX: ALREADY PRESENT")
else:
    assert "run_batch2_contract" in source
    assert "grecbase_fusion_full_head_72_max" in source

    bridge = '''
# CTA_BATCH2_IMPORT_PRIORITY_FIX
import sys as _cta_sys
from pathlib import Path as _cta_Path

_cta_candidate = next((
    p for p in (
        _cta_Path("/batch2/cta_max"),
        _cta_Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
    )
    if (p / "run_batch2_contract.py").is_file()
    and (p / "grecbase_fusion_full_head_72_max.py").is_file()
), None)

if _cta_candidate is None:
    raise ImportError("Corrected CTA batch-2 package unavailable")

_cta_sys.path.insert(0, str(_cta_candidate.parent))
import cta_max as _cta_pkg

_cta_pkg.__path__ = [str(_cta_candidate)] + [
    str(p) for p in _cta_pkg.__path__
    if str(p) != str(_cta_candidate)
]
'''

    tree = ast.parse(source)
    offset = 0

    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and offset == 0
        ):
            offset = node.end_lineno
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
        ):
            offset = node.end_lineno
        else:
            break

    lines = source.splitlines(keepends=True)
    updated = "".join(lines[:offset]) + bridge + "\n" + "".join(lines[offset:])

    ast.parse(updated)

    backup = target.with_suffix(".py.pre_import_fix.bak")
    if backup.exists():
        raise SystemExit("STOP: Backup already exists")

    if shutil.disk_usage(target.parent).free < 10 * 1024 * 1024:
        raise SystemExit("STOP: Insufficient disk space")

    shutil.copy2(target, backup)
    target.write_text(updated)

    print("ISOLATED IMPORT FIX: INSTALLED")
    print("BACKUP: PRESERVED")

print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("CONTAINERS: NOT RESTARTED")
print("NEXT: NATIVE BATCH-2 VALIDATION")
PY
