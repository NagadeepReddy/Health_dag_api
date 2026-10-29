python3 - <<'PY'
from pathlib import Path
import ast
import shutil

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = dev / "real_max_batch2_backend.py"
contract = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/run_batch2_contract.py")
backup = dev / "real_max_batch2_backend_before_import_fix.py"

assert backend.is_file(), "Backend missing"
assert contract.is_file(), "Contract missing"
assert not backup.exists(), "STOP: Backup already exists"

old = backend.read_text()
target = "from cta_max.run.batch2_contract import pack_two_requests"
assert old.count(target) == 1, "STOP: Unexpected import statement"

replacement = """import importlib.util as _cta_importlib
from pathlib import Path as _CTAPath

_cta_contract = _CTAPath(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/run_batch2_contract.py"
)
_cta_spec = _cta_importlib.spec_from_file_location(
    "cta_batch2_contract_dev", _cta_contract
)
assert _cta_spec is not None and _cta_spec.loader is not None
_cta_module = _cta_importlib.module_from_spec(_cta_spec)
_cta_spec.loader.exec_module(_cta_module)
pack_two_requests = _cta_module.pack_two_requests"""

updated = old.replace(target, replacement)
ast.parse(updated)

shutil.copy2(backend, backup)
backend.write_text(updated)

print("BACKUP:", backup)
print("IMPORT FIX: INSTALLED")
print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
