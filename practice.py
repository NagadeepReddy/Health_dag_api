
cd /application1/sajjna8 && python3 - <<'PY'
import ast
import re
import shutil
import tempfile
from pathlib import Path

root = Path("/application1/sajjna8")
source = (
    root / "PZAAS_MAX_CLEAN_HANDOFF_20261106/model/"
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev"
)
shared = root / "max_shared_infra/python/max_runtime_shared"
parent = root / "max_shared_infra/isolated"
target = parent / "pzaas_shared_wiring_v1"

print("=== ISOLATED SHARED MAX LIVE WIRING ===")

required = [
    "scheduler_hooks.py",
    "router_contract.py",
    "worker_lifecycle.py",
]

for name in required:
    if not (shared / name).is_file():
        raise SystemExit(f"STOP: Shared component missing: {name}")

if not source.is_dir():
    raise SystemExit("STOP: Original clean PZAAS serving package missing")

if target.exists():
    raise SystemExit("STOP: Existing isolated stage preserved; no overwrite")

parent.mkdir(parents=True, exist_ok=True)

def replace_once(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(
            f"STOP: Expected one exact match in {path.name}: {old}"
        )
    path.write_text(text.replace(old, new, 1))

def replace_line(path, pattern, replacement):
    text = path.read_text()
    matches = list(re.finditer(pattern, text, flags=re.MULTILINE))
    if len(matches) != 1:
        raise RuntimeError(
            f"STOP: Expected one matching line in {path.name}"
        )
    match = matches[0]
    indentation = match.group(1)
    new = "\n".join(
        indentation + line if line else ""
        for line in replacement.splitlines()
    )
    path.write_text(text[:match.start()] + new + text[match.end():])

with tempfile.TemporaryDirectory(
    prefix=".pzaas_shared_build_", dir=parent
) as temporary:
    stage = Path(temporary) / "pzaas_native_serve_dev"
    shutil.copytree(source, stage)

    launcher = stage / "pzaas_native_launcher.py"
    spawn = stage / "pzaas_spawn_worker.py"

    replace_once(
        launcher,
        "from pzaas_native_serve_dev.pzaas_router import register_pzaas_routes",
        "\n".join([
            "from pzaas_native_serve_dev.pzaas_router import pzaas_predict",
            "    from max_runtime_shared.router_contract import RouteBinding, register_model_routes",
            "    from max.serve import api_server as max_api_server",
            "    from max.serve.api_server import ROUTES",
        ]),
    )

    replace_line(
        launcher,
        r"^([ \t]*)register_pzaas_routes\(\)[ \t]*$",
        '\n'.join([
            "register_model_routes(",
            '    ROUTES[max_api_server.APIType.KSERVE].router,',
            '    (RouteBinding("/pzaas/predict", pzaas_predict),),',
            ")",
        ]),
    )

    replace_line(
        spawn,
        r"^([ \t]*)pipeline = worker\.initialize\(\)[ \t]*$",
        '\n'.join([
            "from max_runtime_shared.worker_lifecycle import WorkerLifecycle",
            "lifecycle = WorkerLifecycle(",
            "    create=worker.pipeline_factory,",
            "    load=lambda obj: obj.load(),",
            "    attach_max=worker.attach_max,",
            ")",
            "pipeline = lifecycle.start()",
            "worker.pipeline = pipeline",
        ]),
    )

    replace_line(
        spawn,
        r"^([ \t]*)install_pzaas_scheduler_hook\(\)[ \t]*$",
        '\n'.join([
            "from max_runtime_shared.scheduler_hooks import (",
            "    SchedulerHooks, SharedSchedulerRegistry,",
            ")",
            "registry = SharedSchedulerRegistry()",
            "registry.register(SchedulerHooks(",
            '    model_key="pzaas-v1.472",',
            "    install_queue=install,",
            "    install_scheduler=install_pzaas_scheduler_hook,",
            "))",
            'registry.activate("pzaas-v1.472")',
        ]),
    )

    for name in (
        "pzaas_native_launcher.py",
        "pzaas_spawn_worker.py",
    ):
        ast.parse((stage / name).read_text(), filename=name)

    shutil.move(str(stage), str(target))

print("SHARED ROUTER: WIRED IN ISOLATED STAGE")
print("SHARED WORKER LIFECYCLE: WIRED IN ISOLATED STAGE")
print("SHARED SCHEDULER REGISTRY: WIRED IN ISOLATED STAGE")
print("ORIGINAL QUEUE INSTALL: PRESERVED")
print("ORIGINAL PZAAS HANDOFF: UNCHANGED")
print("CTA / BPLAN HANDOFFS: UNCHANGED")
print("NO TRAINED WEIGHTS DUPLICATED")
print("NO CONTAINERS STARTED")
print("STAGE:", target)
print("NEXT: ISOLATED LIVE MAX HTTP VERIFICATION")
PY
