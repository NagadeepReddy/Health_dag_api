cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path
import ast
import json

root = Path("/application1")
repo = Path.cwd()

adapter = root / (
    "CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2/cta_worker_adapter.py"
)

sample = repo / (
    "artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

assert adapter.is_file(), "STOP: Adapter missing"
assert sample.is_file(), "STOP: CTA JSON missing"

source = adapter.read_text()
tree = ast.parse(source)

methods = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef)
    and n.name == "predict_batch"
]

assert len(methods) == 1, "STOP: Batch method mismatch"

node = methods[0]
lines = source.splitlines()

print("=== REAL CTA REQUEST ===")
body = json.loads(sample.read_text())

print("ROOT TYPE:", type(body).__name__)
print("ROOT KEYS:", sorted(body) if isinstance(body, dict) else "N/A")

print("\n=== BATCH ADAPTER ROUTING ===")

for number in range(node.lineno, node.end_lineno + 1):
    line = lines[number - 1]

    if any(x in line for x in (
        "model_base =",
        "model_atc =",
        "predict_raw(",
        "infer_max_batch(",
        "cached_preprocess",
        "original_preprocess",
        "request_context",
        "model.calls",
    )):
        print(f"{number}: {line.strip()}")

print("\nREAD-ONLY CHECK COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
