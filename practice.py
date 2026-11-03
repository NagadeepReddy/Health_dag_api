cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/BPLAN_MAX_FINAL_TEAM_HANDOFF_20261102/artifacts/v1.113-max/maxserve_bplan_extension")
files = [
    root/"bplan_native_serve_dev/bplan_spawn_worker.py",
    root/"bplan_max_dev/bplan_native_worker_adapter.py",
    root/"bplan_max_dev/bplan_max_model_adapter.py",
]
for p in files:
    print(f"\n=== {p.name} ===")
    if not p.is_file():
        print("MISSING")
        continue
    lines = p.read_text().splitlines()
    tree = ast.parse("\n".join(lines))
    for n in ast.walk(tree):
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            print(f"{n.lineno}: {type(n).__name__} {n.name}")
    print("--- Model execution references ---")
    count = 0
    for i, line in enumerate(lines, 1):
        if any(x in line.lower() for x in (
            "predict_raw(", "execute(", "model_path",
            "pipeline(", "v1.113", "model_adapter",
            "max_backend", "max_model"
        )):
            print(f"{i}: {line.strip()[:160]}")
            count += 1
            if count >= 35:
                break
PY
