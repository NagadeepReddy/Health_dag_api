python3 - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2/cta_worker_adapter.py"
)

assert p.is_file(), "STOP: Adapter missing"
source = p.read_text()
tree = ast.parse(source)

method = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef)
    and n.name == "predict_batch"
)

print("=== CURRENT ADAPTER IMPLEMENTATION ===")

for number, line in enumerate(source.splitlines(), 1):
    if method.lineno <= number <= method.end_lineno:
        if any(x in line for x in (
            "preprocess",
            "predict_raw",
            "model.calls",
            "model_base",
            "model_atc",
            "finally:",
            "cached_result",
            "infer_max_batch",
        )):
            print(f"{number}: {line.strip()}")

print("CACHE FIX:", "PRESENT" if "cached_preprocess" in source else "MISSING")
print("BATCH METHOD: PRESENT")
print("SYNTAX: PASS")
print("NO FILES MODIFIED")
PY
