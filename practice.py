
cd /application1/sajjna8 && python3 - <<'PY'
import ast
import re
from pathlib import Path

base = Path("/application1/sajjna8")
stage = base / "max_shared_infra/isolated/cta_shared_wiring_v1"
shared = base / "max_shared_infra/python/max_runtime_shared"

spawn = stage / "cta_spawn_worker.py"
router = stage / "cta_router.py"
launcher = stage / "cta_native_launcher.py"

print("=== CTA SHARED MAX LIVE WIRING ===", flush=True)

required = [
    spawn, router, launcher,
    shared / "worker_lifecycle.py",
    shared / "scheduler_hooks.py",
    shared / "router_contract.py",
]

for path in required:
    if not path.is_file():
        raise SystemExit(f"STOP: Missing required file: {path}")

changes = {}

# Wire shared worker lifecycle and scheduler without replacing
# CTA's original model creation or MAX attachment logic.
source = spawn.read_text()
tree = ast.parse(source)

classes = [
    node for node in tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "CTAFactoryWrapper"
]

if len(classes) != 1:
    raise SystemExit("STOP: CTA factory class not uniquely found")

cls = classes[0]
methods = [
    node for node in cls.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "__call__"
]

if "def _shared_original_call(" in source:
    if "WorkerLifecycle(" not in source:
        raise SystemExit("STOP: Partial shared worker modification")
    print("CTA SHARED WORKER: ALREADY WIRED")
else:
    if len(methods) != 1 or methods[0].decorator_list:
        raise SystemExit("STOP: CTA factory method not safely identified")

    method = methods[0]
    calls = [
        node for node in ast.walk(method)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "install_cta_scheduler_hook"
    ]

    if len(calls) != 1 or calls[0].lineno != calls[0].end_lineno:
        raise SystemExit("STOP: CTA scheduler call not uniquely identified")

    lines = source.splitlines(keepends=True)
    header = lines[method.lineno - 1]

    if "def __call__(" not in header:
        raise SystemExit("STOP: Unexpected CTA factory definition")

    lines[method.lineno - 1] = header.replace(
        "def __call__(",
        "def _shared_original_call(",
        1
    )

    wrapper = '''
    def __call__(self, *args, **kwargs):
        from max_runtime_shared.worker_lifecycle import WorkerLifecycle
        lifecycle = WorkerLifecycle(
            create=lambda: self._shared_original_call(*args, **kwargs),
            load=lambda existing: None,
            attach_max=lambda existing: None,
        )
        return lifecycle.start()
'''

    lines[method.end_lineno:method.end_lineno] = [wrapper]

    # The existing CTA launcher already installs its native queue.
    # Shared registration invokes the same original scheduler hook.
    hook = calls[0]
    original_line = lines[hook.lineno - 1]
    indent = re.match(r"[ \t]*", original_line).group()

    scheduler = "\n".join([
        indent + "from max_runtime_shared.scheduler_hooks import SchedulerHooks, SharedSchedulerRegistry",
        indent + "shared_registry = SharedSchedulerRegistry()",
        indent + "shared_registry.register(SchedulerHooks(",
        indent + '    model_key="cta-v1.168",',
        indent + "    install_queue=lambda: None,",
        indent + "    install_scheduler=install_cta_scheduler_hook,",
        indent + "))",
        indent + 'shared_registry.activate("cta-v1.168")',
        "",
    ])

    lines[hook.lineno - 1:hook.end_lineno] = [scheduler]
    updated = "".join(lines)

    ast.parse(updated)
    changes[spawn] = updated

# Register existing CTA endpoints through the shared router.
source = router.read_text()

if "register_model_routes(" in source:
    if "from max_runtime_shared.router_contract import" not in source:
        raise SystemExit("STOP: Partial shared router modification")
    print("CTA SHARED ROUTER: ALREADY WIRED")
else:
    tree = ast.parse(source)
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "register_cta_routes"
    ]

    if len(functions) != 1:
        raise SystemExit("STOP: CTA route function not uniquely found")

    calls = []
    for node in functions[0].body:
        if not isinstance(node, ast.Expr):
            continue

        call = node.value
        if not isinstance(call, ast.Call):
            continue

        if not isinstance(call.func, ast.Attribute):
            continue

        if call.func.attr != "add_api_route":
            continue

        if len(call.args) < 2:
            raise SystemExit("STOP: CTA route arguments incomplete")

        path = call.args[0]
        if not isinstance(path, ast.Constant):
            raise SystemExit("STOP: Dynamic CTA route requires review")

        if not isinstance(path.value, str):
            raise SystemExit("STOP: Unexpected CTA route path")

        methods = next(
            (kw.value for kw in call.keywords
             if kw.arg == "methods"),
            None
        )

        if not isinstance(methods, (ast.List, ast.Tuple)):
            raise SystemExit("STOP: CTA route methods need review")

        values = [
            element.value for element in methods.elts
            if isinstance(element, ast.Constant)
            and isinstance(element.value, str)
        ]

        if len(values) != len(methods.elts):
            raise SystemExit("STOP: Dynamic methods need review")

        calls.append((
            node,
            path.value,
            ast.unparse(call.args[1]),
            tuple(values)
        ))

    paths = {path for _, path, _, _ in calls}

    if not {"/cta/infer", "/cta/predict"}.issubset(paths):
        raise SystemExit("STOP: Required CTA routes not found")

    lines = source.splitlines(keepends=True)

    for index in range(len(calls) - 1, -1, -1):
        node, path, handler, methods = calls[index]
        indent = re.match(
            r"[ \t]*", lines[node.lineno - 1]
        ).group()

        replacement = []

        if index == 0:
            replacement.append(
                indent +
                "from max_runtime_shared.router_contract import RouteBinding, register_model_routes"
            )

        replacement.extend([
            indent + "register_model_routes(",
            indent + "    router,",
            indent + "    [RouteBinding(",
            indent + f"        path={path!r},",
            indent + f"        endpoint={handler},",
            indent + f"        methods={methods!r},",
            indent + "    )],",
            indent + ")",
        ])

        lines[node.lineno - 1:node.end_lineno] = [
            "\n".join(replacement) + "\n"
        ]

    updated = "".join(lines)
    ast.parse(updated)
    changes[router] = updated

# Validate everything before saving.
for path, content in changes.items():
    compile(content, str(path), "exec")

for path, content in changes.items():
    path.write_text(content)
    print("UPDATED:", path.name)

print("\n=== RESULT ===")
print("CTA SHARED WORKER LIFECYCLE: WIRED")
print("CTA SHARED SCHEDULER REGISTRY: WIRED")
print("ORIGINAL CTA QUEUE INITIALIZATION: PRESERVED")
print("CTA SHARED ROUTER: WIRED")
print("ISOLATED PYTHON SYNTAX: PASS")
print("ORIGINAL CTA / BPLAN / PZAAS: UNCHANGED")
print("NO CONTAINERS STARTED")
print("NEXT: LIVE CTA HTTP AND COMBINED THREE-MODEL VALIDATION")
PY
