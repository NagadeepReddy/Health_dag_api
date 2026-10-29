python3 - <<'PY'
from pathlib import Path
import ast

root = Path("/application1")
repo = root / "sajjna8/rt-pzaas-cta-offers-v1"
working = repo / "artifacts/v1.168-max/maxserve_cta_extension"
dev = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029"

files = {
    "WORKING ADAPTER": working / "cta_worker_adapter.py",
    "BATCH-2 ADAPTER": dev / "native_batch2/cta_worker_adapter.py",
    "WORKER SPAWN": working / "cta_spawn_worker.py",
    "WORKER REGISTRATION": working / "cta_worker_registration.py",
}

for label, path in files.items():
    print(f"\n=== {label} ===")
    if not path.is_file():
        print("MISSING:", path)
        continue

    source = path.read_text()
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print("CLASS:", node.name)
            print("METHODS:", [
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ])

    if "WORKER" in label:
        for i, line in enumerate(source.splitlines(), 1):
            if any(x in line for x in (
                "Adapter", "_cta_adapter",
                "create_cta_scheduler", "load_scheduler"
            )):
                print(f"{i}: {line.strip()}")

stage = dev / "native_batch2_live_stage"
print("\nSTAGE EXISTS:", stage.exists())
print("NO FILES MODIFIED")
PY
