python3 - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

files = [
    base / "native_batch2/cta_worker_adapter.py",
    base / "native_batch2/cta_native_scheduler.py",
    base / "real_max_batch2_backend.py",
]

for p in files:
    print("\n===== " + p.name + " =====")
    if not p.is_file():
        print("MISSING:", p)
        continue

    source = p.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()

    print("FUNCTIONS:")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(x in node.name.lower() for x in
                   ("predict", "batch", "infer", "dispatch", "execute")):
                print(f"  {node.lineno}: {node.name}")

    print("INTEGRATION POINTS:")
    keywords = (
        "real_max_batch2_backend",
        "predict_batch",
        "infer_max_batch",
        "model.execute",
        "batch2_contract",
        "request_id",
    )

    matches = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if any(k in line for k in keywords)
    ]

    for i, line in matches[:35]:
        print(f"  {i}: {line[:180]}")

print("\nINSPECTION COMPLETE")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
