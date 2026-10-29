python3 - <<'PY'
from pathlib import Path
import ast
import shutil

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
adapter = dev / "native_batch2/cta_worker_adapter.py"
candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
backup = adapter.with_name(
    "cta_worker_adapter_before_package_bridge_20261029.py"
)

assert adapter.is_file(), "STOP: Adapter missing"
assert (candidate / "run_batch2_contract.py").is_file(), \
    "STOP: Verified contract path unavailable"
assert not backup.exists(), "STOP: Backup already exists"

source = adapter.read_text()

old = "            spec.loader.exec_module(module)"

new = '''            import cta_max as _cta_pkg
            _candidate_pkg = Path(
                "/application1/cta_max_true_batch_dev_20261028/"
                "batch2_candidate/cta_max"
            )
            if str(_candidate_pkg) not in _cta_pkg.__path__:
                _cta_pkg.__path__.append(str(_candidate_pkg))
            spec.loader.exec_module(module)'''

assert source.count(old) == 1, \
    "STOP: Expected backend loader not found exactly once"

updated = source.replace(old, new)
ast.parse(updated)

shutil.copy2(adapter, backup)
adapter.write_text(updated)

print("BACKUP: CREATED")
print("DEVELOPMENT PACKAGE BRIDGE: INSTALLED")
print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
