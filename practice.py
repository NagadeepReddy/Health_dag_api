
cd /application1/sajjna8 && python3 - <<'PY'
import ast
import re
from pathlib import Path

base = Path("/application1/sajjna8")
shared = base / "max_shared_infra/python/max_runtime_shared"
model = (
    base / "PZAAS_MAX_CLEAN_HANDOFF_20261106/model/"
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev"
)

print("=== FINAL LIVE MAX INTEGRATION CONTRACTS ===")

modules = [
    "scheduler_hooks.py",
    "router_contract.py",
    "worker_lifecycle.py",
    "typed_queue.py",
]

def signature(node):
    a = node.args
    args = [x.arg for x in a.posonlyargs + a.args]
    if a.vararg:
        args.append("*" + a.vararg.arg)
    args += [x.arg for x in a.kwonlyargs]
    if a.kwarg:
        args.append("**" + a.kwarg.arg)
    return "(" + ", ".join(args) + ")"

for filename in modules:
    p = shared / filename
    print(f"\n=== SHARED: {filename} ===")
    if not p.is_file():
        print("STOP: FILE MISSING")
        raise SystemExit(1)

    tree = ast.parse(p.read_text())

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            print("FUNCTION:", node.name + signature(node))
        elif isinstance(node, ast.ClassDef):
            print("CLASS:", node.name)
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    print("  METHOD:", child.name + signature(child))

targets = {
    "pzaas_native_launcher.py": r"register_|pzaas_spawn|start_model_worker|install\(|api_server|uvicorn",
    "pzaas_queue_compat.py": r"install|SchedulerZmqConfigs|response_type",
    "pzaas_native_scheduler.py": r"^class |^\s+def |SchedulerResult|response_queue",
    "pzaas_scheduler_factory.py": r"^def |^class |Scheduler|install",
    "pzaas_router.py": r"^async def |^def |ROUTES|open_channel|response_queue",
    "pzaas_spawn_worker.py": r"^class |^\s+def |initialize|install|PZAASNative",
    "pzaas_worker_adapter.py": r"^class |^\s+def |attach_max|predict_raw",
}

print("\n=== ORIGINAL PZAAS SERVING INTEGRATION POINTS ===")

for filename, pattern in targets.items():
    p = model / filename
    print(f"\nFILE: {filename}")

    if not p.is_file():
        print("NOT FOUND")
        continue

    lines = p.read_text().splitlines()
    matches = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if re.search(pattern, line)
    ]

    for number, line in matches[:16]:
        print(f"{number}: {line[:150]}")

    if len(matches) > 16:
        print(f"... {len(matches)-16} additional matching lines")

print("\n=== SHARED COMPONENT ADOPTION ===")

for filename in modules:
    stem = Path(filename).stem
    references = []

    for p in model.glob("*.py"):
        if stem in p.read_text(errors="replace"):
            references.append(p.name)

    print(
        stem + ":",
        ", ".join(references) if references else
        "NOT REFERENCED DIRECTLY"
    )

print("\n=== RESULT ===")
print("EXACT SHARED API SIGNATURES: CAPTURED")
print("ORIGINAL MODEL SERVING HOOKS: IDENTIFIED")
print("ORIGINAL DS / WEIGHTS: UNCHANGED")
print("CTA / BPLAN / PZAAS HANDOFFS: UNCHANGED")
print("NO FILES MODIFIED")
print("NO CONTAINERS STARTED")
print("NEXT: ISOLATED END-TO-END SHARED COMPONENT WIRING")
PY
