python3 - <<'PY'
import ast
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

files = [
    base / "native_batch2_cached_overlay/cta_worker_adapter.py",
    base / "native_batch2_cached_overlay/cta_native_scheduler.py",
    base / "real_max_batch2_backend.py",
]

for path in files:
    print(f"\n=== {path.name} ===", flush=True)
    if not path.is_file():
        print("FILE NOT FOUND")
        continue

    lines = path.read_text().splitlines()
    tree = ast.parse("\n".join(lines))
    selected = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in ("predict_batch", "infer_max_batch"):
                start = max(node.lineno, node.end_lineno - 55)
                selected.update(range(start, node.end_lineno + 1))

    for i, line in enumerate(lines, 1):
        if any(x in line for x in (
            "TWO JSON RESPONSES PRODUCED",
            "response_queue.put_nowait",
            "CTA WORKER RESPONSE IDS",
        )):
            selected.update(range(max(1, i-5), min(len(lines), i+12)+1))

    for i in sorted(selected):
        print(f"{i}: {lines[i-1]}")

print("\nTARGETED RETURN-PATH INSPECTION: COMPLETE")
print("NO FILES MODIFIED")
PY
