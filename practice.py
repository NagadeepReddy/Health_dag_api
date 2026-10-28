cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/maxserve_cta_extension")

for name in (
    "cta_native_scheduler.py",
    "cta_worker_adapter.py",
):
    p = base / name
    print(f"\n=== {name} ===")

    tree = ast.parse(p.read_text())

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in (
                "run_iteration",
                "predict",
                "predict_batch",
                "batch_predict",
                "infer_batch",
            ):
                print(f"\nFUNCTION: {node.name}")
                print(
                    ast.get_source_segment(
                        p.read_text(), node
                    )[:6500]
                )

print("\n=== BATCH API REFERENCES ===")
for p in base.glob("*.py"):
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if any(x in line.lower() for x in (
            "predict_batch",
            "batch_predict",
            "infer_batch",
            "max_items_per_iteration",
        )):
            print(f"{p.name}:{i}: {line.strip()}")

print("\nBATCH CAPABILITY INSPECTION: COMPLETE")
print("NO FILES MODIFIED")
print("MAX MODEL NOT STARTED")
PY
