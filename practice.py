PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, shutil
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
target = base / "real_max_batch2_backend.py"
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")

assert target.is_file(), "STOP: Backend missing"
assert (candidate / "run/batch2_contract.py").is_file(), "STOP: Batch contract missing"
assert (candidate / "grecbase_fusion_full_head_72_max.py").is_file(), "STOP: Corrected graph missing"

source = target.read_text()
marker = "# CTA_BATCH2_IMPORT_PRIORITY_FIX"

assert "grecbase_fusion_full_head_72_max" in source, "STOP: Backend graph selection differs"
assert "run.batch2_contract" in source, "STOP: Backend contract differs"

if marker in source:
    print("IMPORT PRIORITY FIX: ALREADY INSTALLED")
else:
    bridge = '''
# CTA_BATCH2_IMPORT_PRIORITY_FIX
import sys as _cta_sys
from pathlib import Path as _cta_Path

_cta_candidate = next((
    p for p in (
        _cta_Path("/batch2/cta_max"),
        _cta_Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
    )
    if (p / "run/batch2_contract.py").is_file()
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

if "cta_max.run" in _cta_sys.modules:
    _cta_run = _cta_sys.modules["cta_max.run"]
    _run_path = str(_cta_candidate / "run")
    _cta_run.__path__ = [_run_path] + [
        str(p) for p in _cta_run.__path__
        if str(p) != _run_path
    ]
'''

    tree = ast.parse(source)
    offset = 0

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and offset == 0:
            offset = node.end_lineno
        elif isinstance(node, ast.ImportFrom) and node.module == "__future__":
            offset = node.end_lineno
        else:
            break

    lines = source.splitlines(keepends=True)
    updated = "".join(lines[:offset]) + bridge + "\n" + "".join(lines[offset:])
    ast.parse(updated)

    backup = target.with_name(target.name + ".pre_batch2_import_fix.bak")
    assert not backup.exists(), "STOP: Backup already exists"
    shutil.copy2(target, backup)
    target.write_text(updated)

    print("ISOLATED IMPORT PRIORITY: FIX INSTALLED")
    print("BACKUP: PRESERVED")

print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("WORKING MAX: UNCHANGED")
print("CONTAINERS: NOT RESTARTED")
print("NATIVE BATCH-2 HTTP: PENDING")
PY
