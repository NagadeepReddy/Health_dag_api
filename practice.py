cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/BPLAN_MAX_FINAL_TEAM_HANDOFF_20261102/artifacts/v1.113-max/maxserve_bplan_extension")

names = [
    "bplan_native_launcher.py",
    "bplan_router.py",
    "bplan_pipeline_model.py",
    "bplan_native_scheduler.py",
    "bplan_http_pipeline.py",
    "bplan_spawn_worker.py",
]

for name in names:
    p = root/"bplan_native_serve_dev"/name
    print(f"\n=== {name} ===")
    if not p.is_file():
        print("MISSING")
        continue
    tree = ast.parse(p.read_text())
    imports = sorted(set(
        n.module for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module
    ))
    for mod in imports:
        print("IMPORT:", mod)
    refs = sorted(set(
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and any(x in n.value.lower() for x in
                ("v1.113", "/bplan", "bplan_max", "/workspace"))
    ))
    for ref in refs[:12]:
        print("REFERENCE:", ref[:150])

print("\n=== MODEL ADAPTER FILES ===")
for p in sorted(root.rglob("*adapter*.py")):
    print(p.relative_to(root))
PY
