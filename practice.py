PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")

targets = [
    base / "real_max_batch2_backend.py",
    candidate / "run_batch2_contract.py",
    candidate / "run/batch2_contract.py",
]

if candidate.is_dir():
    targets += list(candidate.rglob("*.py"))

seen = set()
names = {
    "infer_max_batch",
    "build_grecbase_fusion_graph_order_correct",
    "pack_two_requests",
}

print("=== TARGETED GRAPH CONTRACT CHECK ===")

for path in targets:
    if path in seen or not path.is_file():
        continue
    seen.add(path)

    if path.stat().st_size > 500000:
        continue

    src = path.read_text(errors="replace")
    lines = src.splitlines()

    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in names:
                print(f"\n=== {path} :: {node.name} ===")
                start = node.lineno
                end = min(node.end_lineno, start + 150)
                for i in range(start, end + 1):
                    print(f"{i}: {lines[i-1]}")

    if path.name == "real_max_batch2_backend.py":
        print("\n=== GRAPH LOAD / CACHE REFERENCES ===")
        for i, line in enumerate(lines):
            if any(x in line for x in (
                "session.load(",
                "_max_model",
                "graph.inputs",
                "runtime_inputs",
                "build_grecbase_fusion_graph_order_correct"
            )):
                print(f"{i+1}: {line}")

print("\nGRAPH INSPECTION: COMPLETE")
print("FILES MODIFIED: 0")
print("CONTAINERS RESTARTED: 0")
print("ORIGINAL DS: UNCHANGED")
PY
