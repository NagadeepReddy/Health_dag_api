python3 - <<'PY'
from pathlib import Path
import ast

base = Path("/application1")
candidate = base / "cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
backend = base / "CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py"

contract = candidate / "run_batch2_contract.py"

assert contract.is_file(), "Contract missing"
assert backend.is_file(), "Backend missing"

tree = ast.parse(backend.read_text())
imports = [
    node for node in ast.walk(tree)
    if isinstance(node, ast.ImportFrom)
    and node.module == "cta_max.run_batch2_contract"
]

assert len(imports) == 1, "Unexpected backend import"
assert any(
    alias.name == "pack_two_requests"
    for alias in imports[0].names
), "Packer import missing"

ast.parse(contract.read_text())

print("CONTRACT FILE: PASS")
print("BACKEND IMPORT: PASS")
print("CONTRACT SYNTAX: PASS")
print("NEXT: Container package-resolution test")
print("NO FILES MODIFIED")
PY
