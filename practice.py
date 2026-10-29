python3 - <<'PY'
from pathlib import Path
import ast

root = Path("/application1")
repo = root / "sajjna8/rt-pzaas-cta-offers-v1"
pipeline = repo / "artifacts/v1.167/core-artifact/pipeline.py"
adapter = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2/cta_worker_adapter.py"

assert pipeline.is_file(), "STOP: Original pipeline missing"
assert adapter.is_file(), "STOP: Development adapter missing"

tree = ast.parse(pipeline.read_text())
methods = {
    n.name: n
    for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
}

assert "inference" in methods
assert "predict_raw" in methods

inf = methods["inference"]
src = pipeline.read_text().splitlines()

print("=== ORIGINAL INFERENCE BRANCHES ===")
for n in range(inf.lineno, inf.end_lineno + 1):
    line = src[n - 1]
    if any(s in line for s in (
        "request_context_fmt.endswith",
        "model_atc(",
        "model_base(",
        "faiss.knn(",
        "self.inference(",
    )):
        print(f"{n}: {line.strip()}")

print("\n=== DEVELOPMENT ADAPTER ===")
a = adapter.read_text()
for item in (
    "pipeline.model_base = model",
    "pipeline.model_atc = model",
    "pipeline.predict_raw(body)",
    "cached_preprocess",
    "model.calls != 1",
):
    print(f"{item}: {'PRESENT' if item in a else 'MISSING'}")

print("\nORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
