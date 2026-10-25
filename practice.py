cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
files = [
    "cta_native_launcher.py",
    "cta_spawn_worker.py",
    "cta_worker_registration.py",
    "cta_scheduler_factory.py",
    "cta_native_scheduler.py",
    "cta_router.py",
    "cta_http_pipeline.py",
]

for name in files:
    p = base / name
    print(f"\n=== {name} ===")
    if not p.exists():
        print("MISSING")
        continue
    try:
        tree = ast.parse(p.read_text())
        print("SYNTAX: PASS")
        funcs = [
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        print("FUNCTIONS:", ", ".join(funcs[:25]))
    except SyntaxError as e:
        print("SYNTAX ERROR:", e)

print("\n=== REAL JSON INPUT FILES ===")
for root in [
    Path("artifacts/v1.168-max"),
    Path("artifacts/v1.168"),
]:
    if root.exists():
        matches = list(root.rglob("*sanity*.json"))
        matches += list(root.rglob("*request*.json"))
        for p in dict.fromkeys(matches):
            print(p)

print("\n=== NATIVE STARTUP ENTRY ===")
p = base / "cta_native_launcher.py"
if p.exists():
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if any(s in line for s in [
            "install_cta_spawn_entry",
            "install_cta_scheduler",
            "register_cta_routes",
            "run_module",
            "sys.argv",
        ]):
            print(f"{i}: {line.strip()}")
PY
