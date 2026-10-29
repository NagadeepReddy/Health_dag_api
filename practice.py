python3 - <<'PY'
import ast
from pathlib import Path

p = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2/cta_worker_adapter.py"
)

tree = ast.parse(p.read_text())
method = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef)
    and n.name == "predict_batch"
)

calls = []
for node in ast.walk(method):
    if isinstance(node, ast.Call):
        f = node.func
        name = (
            f.attr if isinstance(f, ast.Attribute)
            else f.id if isinstance(f, ast.Name)
            else "unknown"
        )
        if name in (
            "preprocess",
            "original_preprocess",
            "predict_raw",
            "infer_max_batch",
        ):
            calls.append((node.lineno, name))

print("=== BATCH ADAPTER SEMANTIC CHECK ===")
for line, name in sorted(calls):
    print(f"LINE {line}: {name}")

print("PREPROCESS CACHE: NOT IMPLEMENTED")
print("MULTI-INFERENCE HANDLING: NOT IMPLEMENTED")
print("NEXT: Isolated adapter correction")
print("NO FILES MODIFIED")
PY
