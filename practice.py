cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import re

base = Path("/application1/cta_max_true_batch_dev_20261028")
pkg = base / "batch2_candidate/cta_max"
src = pkg / "run_live_max_inference.py"
dst = pkg / "run_batch2_live_max_inference.py"
graph = pkg / "grecbase_fusion_full_head_72_max.py"
contract = base / "maxserve_cta_extension/cta_batch2_contract.py"

assert src.is_file() and graph.is_file() and contract.is_file(), \
    "STOP: Required batch files missing"
assert not dst.exists(), "STOP: Batch runner already exists"

source = src.read_text()
tree = ast.parse(source)

functions = [
    n for n in tree.body
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    and n.name == "infer_max_live"
]
assert len(functions) == 1, "STOP: Inference function differs"

fn = functions[0]

assignments = [
    n for n in ast.walk(fn)
    if isinstance(n, (ast.Assign, ast.AnnAssign))
    and any(
        isinstance(t, ast.Name) and t.id == "arrays"
        for t in (
            n.targets if isinstance(n, ast.Assign)
            else [n.target]
        )
    )
]
assert len(assignments) == 1, \
    "STOP: Cannot safely locate real input preparation"

a = assignments[0]
lines = source.splitlines(keepends=True)
indent = re.match(r"^\s*", lines[a.lineno - 1]).group()
assert "\n" not in indent

insertion = (
    f"{indent}assert len(arrays) == 72, "
    '"Expected 72 CTA inputs"\n'
    f"{indent}from cta_max.run_batch2_contract import "
    "pack_two_requests\n"
    f"{indent}arrays = pack_two_requests(arrays, arrays)\n"
    f'{indent}print("REAL BATCH-2 INPUTS: PASS", '
    'len(arrays), flush=True)\n'
)

# Provide the contract inside the isolated import package.
contract_dst = pkg / "run_batch2_contract.py"
assert not contract_dst.exists(), "STOP: Contract copy exists"

updated = "".join(
    lines[:a.end_lineno]
    + [insertion]
    + lines[a.end_lineno:]
)

updated = updated.replace(
    "def infer_max_live(",
    "def infer_max_batch2_duplicate(",
    1
)

# Keep the original working inference function untouched.
assert updated != source
ast.parse(updated)
ast.parse(contract.read_text())

contract_dst.write_bytes(contract.read_bytes())
dst.write_text(updated)

print("BATCH-2 REAL INPUT RUNNER: CREATED")
print("TWO IDENTICAL REAL REQUESTS: CONFIGURED")
print("MAX GRAPH: ISOLATED CANDIDATE")
print("RUNNER SYNTAX: PASS")
print("TRUE BATCH INFERENCE: NOT YET EXECUTED")
print("WORKING HTTP 200: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
