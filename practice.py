
cd /application1/sajjna8 && python3 - <<'PY'
import ast
import re
from pathlib import Path

base = Path("/application1/sajjna8")
stage = base / "max_shared_infra/isolated/bplan_shared_wiring_v1"
shared = base / "max_shared_infra/python/max_runtime_shared"

spawn = stage / "bplan_spawn_worker.py"
router = stage / "bplan_router.py"

print("=== BPLAN SHARED MAX LIVE WIRING ===", flush=True)

required = [
    spawn, router,
    shared / "worker_lifecycle.py",
    shared / "scheduler_hooks.py",
    shared / "router_contract.py",
    stage / "bplan_queue_compat.py",
    stage / "bplan_worker_registration.py",
]

missing = [str(p) for p in required if not p.is_file()]
if missing:
    raise SystemExit("STOP: Missing required files:\n" + "\n".join(missing))

changes = {}

# 1. Reuse the shared worker lifecycle without changing the
# previously working BPLAN initialize() behavior.
text = spawn.read_text()

if "WorkerLifecycle(" not in text:
    pattern = r"(?m)^([ \t]*)pipeline = worker\.initialize\(\)[ \t]*$"
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise SystemExit("STOP: BPLAN initialization not uniquely found")

    indent = matches[0].group(1)
    replacement = "\n".join([
        indent + "from max_runtime_shared.worker_lifecycle import WorkerLifecycle",
        indent + "lifecycle = WorkerLifecycle(",
        indent + "    create=worker.initialize,",
        indent + "    load=lambda pipeline: None,",
        indent + "    attach_max=lambda pipeline: None,",
        indent + ")",
        indent + "pipeline = lifecycle.start()",
    ])
    text = text[:matches[0].start()] + replacement + text[matches[0].end():]

# 2. Install the existing BPLAN queue and scheduler through
# the reusable shared scheduler registry.
if 'registry.activate("bplan-v1.113")' not in text:
    pattern = r"(?m)^([ \t]*)install_bplan_scheduler_hook\(\)[ \t]*$"
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise SystemExit("STOP: BPLAN scheduler hook not uniquely found")

    indent = matches[0].group(1)
    replacement = "\n".join([
        indent + "from bplan_native_serve_dev.bplan_queue_compat import install as install_queue",
        indent + "from max_runtime_shared.scheduler_hooks import SchedulerHooks, SharedSchedulerRegistry",
        indent + "registry = SharedSchedulerRegistry()",
        indent + "registry.register(SchedulerHooks(",
        indent + '    model_key="bplan-v1.113",',
        indent + "    install_queue=install_queue,",
        indent + "    install_scheduler=install_bplan_scheduler_hook,",
        indent + "))",
        indent + 'registry.activate("bplan-v1.113")',
    ])
    text = text[:matches[0].start()] + replacement + text[matches[0].end():]

compile(text, str(spawn), "exec")
changes[spawn] = text

# 3. Register the original BPLAN handler through the shared
# router contract, using MAX Serve's existing router.
text = router.read_text()

if "register_model_routes(" not in text:
    tree = ast.parse(text)
    candidates = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue

        call = node.value
        if not isinstance(call, ast.Call):
            continue
        if not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr != "add_api_route":
            continue
        if not call.args:
            continue

        path = call.args[0]
        if isinstance(path, ast.Constant) and path.value == "/bplan/predict":
            candidates.append(node)

    if len(candidates) != 1:
        raise SystemExit(
            "STOP: BPLAN route not uniquely identified; "
            "no files modified"
        )

    node = candidates[0]
    if len(node.value.args) < 2:
        raise SystemExit("STOP: BPLAN route handler missing")

    handler = ast.unparse(node.value.args[1])
    lines = text.splitlines(keepends=True)
    indent = re.match(r"[ \t]*", lines[node.lineno - 1]).group()

    replacement = "\n".join([
        indent + "from max_runtime_shared.router_contract import RouteBinding, register_model_routes",
        indent + "register_model_routes(",
        indent + "    router,",
        indent + "    [RouteBinding(",
        indent + '        path="/bplan/predict",',
        indent + f"        endpoint={handler},",
        indent + '        methods=("POST",),',
        indent + "    )],",
        indent + ")",
        "",
    ])

    lines[node.lineno - 1:node.end_lineno] = [replacement]
    text = "".join(lines)

compile(text, str(router), "exec")
changes[router] = text

# Validate all changes before writing any file.
for path, content in changes.items():
    ast.parse(content, filename=str(path))
    compile(content, str(path), "exec")

for path, content in changes.items():
    if path.read_text() != content:
        path.write_text(content)
        print("UPDATED:", path.name)
    else:
        print("ALREADY WIRED:", path.name)

print("\n=== RESULT ===")
print("SHARED WORKER LIFECYCLE: WIRED")
print("SHARED SCHEDULER REGISTRY: WIRED")
print("BPLAN ORIGINAL QUEUE INSTALLER: PRESERVED")
print("SHARED ROUTER: WIRED")
print("ISOLATED PYTHON SYNTAX: PASS")
print("ORIGINAL BPLAN HANDOFF: UNCHANGED")
print("ORIGINAL DS / CTA / PZAAS: UNCHANGED")
print("NO CONTAINERS STARTED")
print("NEXT: LIVE BPLAN SHARED MAX HTTP VALIDATION")
PY
