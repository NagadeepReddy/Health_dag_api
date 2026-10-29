python3 - <<'PY'
from pathlib import Path
import ast

base = Path("/application1")
candidate = base / "cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
backend = base / "CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py"

contract = candidate / "run/batch2_contract.py"

assert contract.is_file(), "Candidate contract missing"
assert backend.is_file(), "Backend missing"

tree = ast.parse(backend.read_text())

imports = [
    (node.module, [alias.name for alias in node.names])
    for node in ast.walk(tree)
    if isinstance(node, ast.ImportFrom)
    and node.module
    and "batch2_contract" in node.module
]

print("CONTRACT:", contract)
print("BACKEND IMPORTS:", imports)

assert any(
    module == "cta_max.run.batch2_contract"
    and "pack_two_requests" in names
    for module, names in imports
), "Unexpected backend import"

ast.parse(contract.read_text())
print("CONTRACT SYNTAX: PASS")
print("BACKEND IMPORT TARGET: CONFIRMED")
print("NO FILES MODIFIED")
PY
