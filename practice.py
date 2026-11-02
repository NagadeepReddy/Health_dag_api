python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
ext = root / "artifacts/v1.113-max/maxserve_bplan_extension"

files = {
    "Native worker adapter": ext / "bplan_max_dev/bplan_native_worker_adapter.py",
    "MAX model adapter": ext / "bplan_max_dev/bplan_max_model_adapter.py",
    "Native scheduler": ext / "bplan_native_serve_dev/bplan_native_scheduler.py",
    "Original DS pipeline": root / "artifacts/v1.113/core-artifact/pipeline.py",
}

for name, path in files.items():
    print(f"\n=== {name} ===")
    if not path.is_file():
        print("FILE MISSING:", path)
        continue

    tree = ast.parse(path.read_text())
    methods = {
        node.name: node.lineno
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    for method in (
        "predict_batch", "predict", "__call__",
        "run_iteration", "inference_batch", "predict_raw"
    ):
        if method in methods:
            print(f"{method}: line {methods[method]}")

    if name == "Native scheduler":
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if any(s in line for s in (
                "max_items_per_iteration", "predict_batch",
                "len(active)", "batch_fn"
            )):
                print(f"{number}: {line.strip()[:140]}")

print("\nREAD-ONLY CHECK COMPLETE")
PY
