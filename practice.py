python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py")
helper = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/run_batch2_contract.py")

if not p.is_file() or not helper.is_file():
    raise SystemExit("STOP: Backend or original batch helper not found")

src = p.read_text()
old = "from cta_max.run_batch2_contract import pack_two_requests"

if src.count(old) != 1:
    raise SystemExit("STOP: Expected import not found exactly once")

lines = src.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if old in line)
indent = lines[index][:len(lines[index]) - len(lines[index].lstrip())]

replacement = [
    "import importlib.util as _batch_import_util",
    "_batch_helper = _cta_candidate / 'run_batch2_contract.py'",
    "_batch_spec = _batch_import_util.spec_from_file_location(",
    "    'cta_max.run_batch2_contract', _batch_helper)",
    "_batch_module = _batch_import_util.module_from_spec(_batch_spec)",
    "_batch_spec.loader.exec_module(_batch_module)",
    "pack_two_requests = _batch_module.pack_two_requests",
]

new_line = "".join(indent + line + "\n" for line in replacement)
updated = "".join(lines[:index] + [new_line] + lines[index+1:])

ast.parse(updated)

backup = p.with_name(p.name + ".before_helper_import_fix")
if backup.exists():
    raise SystemExit("STOP: Backup already exists; no changes made")

shutil.copy2(p, backup)
p.write_text(updated)

print("BATCH-2 HELPER IMPORT FIX: INSTALLED")
print("SYNTAX: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
