cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("/application1/cta_max_true_batch_dev_20261028")
pkg = base / "batch2_candidate/cta_max"
src = pkg / "run_live_max_inference.py"
dst = pkg / "run_batch2_live_max_inference.py"
contract = base / "maxserve_cta_extension/cta_batch2_contract.py"
contract_dst = pkg / "run_batch2_contract.py"

assert src.is_file(), "STOP: Live inference source missing"
assert contract.is_file(), "STOP: Batch contract missing"
assert not dst.exists(), "STOP: Batch runner already exists"
assert not contract_dst.exists(), "STOP: Batch contract copy already exists"
assert shutil.disk_usage("/application1").free > 1024**3, \
    "STOP: Insufficient disk space"

source = src.read_text()
tree = ast.parse(source)

functions = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == "infer_max_live"
]
assert len(functions) == 1, "STOP: Inference function differs"
fn = functions[0]

def contains_arrays(target):
    return any(
        isinstance(n, ast.Name) and n.id == "arrays"
        for n in ast.walk(target)
    )

assignments = []
for node in ast.walk(fn):
    if isinstance(node, ast.Assign):
        if any(contains_arrays(t) for t in node.targets):
            assignments.append(node)
    elif isinstance(node, ast.AnnAssign):
        if contains_arrays(node.target):
            assignments.append(node)

assert len(assignments) == 1, (
    f"STOP: Expected one arrays assignment, found {len(assignments)}"
)

assignment = assignments[0]
lines = source.splitlines(keepends=True)
indent = " " * assignment.col_offset

insertion = (
    f'{indent}assert len(arrays) == 72, "Expected 72 CTA inputs"\n'
    f'{indent}from cta_max.run_batch2_contract import pack_two_requests\n'
    f'{indent}arrays = pack_two_requests(arrays, arrays)\n'
    f'{indent}print("REAL BATCH-2 INPUTS: PASS", '
    'len(arrays), flush=True)\n'
)

updated = "".join(
    lines[:assignment.end_lineno]
    + [insertion]
    + lines[assignment.end_lineno:]
)

ast.parse(updated)
ast.parse(contract.read_text())

# Write only to the isolated batch development candidate.
contract_dst.write_bytes(contract.read_bytes())
dst.write_text(updated)

print("BATCH-2 RUNNER: CREATED")
print("ARRAY ASSIGNMENT LINE:", assignment.lineno)
print("72-INPUT PACKING: CONFIGURED")
print("PYTHON SYNTAX: PASS")
print("RUNNER:", dst)
print("REAL BATCH EXECUTION: NOT YET TESTED")
print("WORKING HTTP 200: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
