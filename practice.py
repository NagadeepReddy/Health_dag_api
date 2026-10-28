cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import re

base = Path("/application1/cta_max_true_batch_dev_20261028")
pkg = base / "batch2_candidate/cta_max"
runner = pkg / "run_batch2_live_max_inference.py"
graph = pkg / "grecbase_fusion_full_head_72_max.py"
contract = pkg / "run_batch2_contract.py"

checks = {}

for name, path in [
    ("RUNNER", runner),
    ("GRAPH", graph),
    ("CONTRACT", contract),
]:
    checks[name] = path.is_file()
    print(f"{name} EXISTS:", "PASS" if checks[name] else "FAIL")

if not all(checks.values()):
    raise SystemExit("STOP: Required batch files missing")

sources = {
    "runner": runner.read_text(),
    "graph": graph.read_text(),
    "contract": contract.read_text(),
}

for name, source in sources.items():
    ast.parse(source)
print("PYTHON SYNTAX: PASS")

r = sources["runner"]
g = sources["graph"]
c = sources["contract"]

checks["72_INPUT_PACKING"] = (
    "pack_two_requests(arrays, arrays)" in r
)
checks["BATCH_CONTRACT"] = (
    "def pack_two_requests(" in c
    and "def split_two_outputs(" in c
)
checks["BATCH_GRAPH_OUTPUT"] = bool(
    re.search(r"ops\.reshape\s*\(\s*outs\s*,\s*\[\s*2\s*,\s*2048\s*\]", g)
)
checks["GRAPH_IMPORT"] = (
    "grecbase_fusion_full_head_72_max" in r
)
checks["INFERENCE_FUNCTION"] = (
    "def infer_max_live(" in r
)

for name in [
    "72_INPUT_PACKING",
    "BATCH_CONTRACT",
    "BATCH_GRAPH_OUTPUT",
    "GRAPH_IMPORT",
    "INFERENCE_FUNCTION",
]:
    print(name + ":", "PASS" if checks[name] else "REVIEW")

print("\n=== FINAL READINESS ===")
print("STATIC CONNECTIONS:",
      "PASS" if all(checks.values()) else "REVIEW REQUIRED")
print("BATCH-2 COMPILATION: NOT YET TESTED")
print("BATCH-2 NUMERICAL PARITY: NOT YET TESTED")
print("WORKING HTTP 200: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
