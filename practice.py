
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
IMAGE="localhost/max-shared-runtime:cpu"

test -f "$ROOT/python/max_runtime_shared/typed_queue.py"

podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=4g --pids-limit=256 \
  -v "$ROOT/python:/shared_runtime:ro" \
  -w /shared_runtime \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_runtime \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" -u - <<'PY'
import importlib
import inspect
from pathlib import Path

print("=== INSTALLED MAX API INSPECTION ===")

targets = [
    ("max.serve.scheduler.queues", "SchedulerZmqConfigs"),
    ("max.serve.queue.zmq_queue", "ZmqConfig"),
    ("max.interfaces.request", "RequestID"),
    ("max.interfaces.scheduler", "SchedulerResult"),
    ("max.pipelines.core", "PipelineTask"),
]

for module_name, symbol in targets:
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, symbol, None)

        if obj is None:
            print(f"{symbol}: NOT EXPORTED from {module_name}")
            continue

        print(f"{symbol}: FOUND in {module_name}")

        if inspect.isclass(obj):
            try:
                print("  SIGNATURE:", inspect.signature(obj))
            except (TypeError, ValueError):
                pass

            if symbol == "SchedulerZmqConfigs":
                try:
                    print("  INITIALIZER:")
                    for line in inspect.getsource(
                        obj.__init__
                    ).splitlines()[:35]:
                        print("   ", line)
                except (OSError, TypeError):
                    print("  Source unavailable")

    except Exception as exc:
        print(
            f"{symbol}: IMPORT ERROR:",
            type(exc).__name__,
            str(exc)[:250]
        )

print("\n=== PIPELINE TASK DEFINITION SEARCH ===")

root = Path("/opt/venv/lib/python3.12/site-packages/max")

found = 0

for path in sorted(root.rglob("*.py")):
    if not (
        "pipeline" in path.parts
        or "serve" in path.parts
    ):
        continue

    try:
        lines = path.read_text(
            errors="replace"
        ).splitlines()
    except OSError:
        continue

    for number, line in enumerate(lines, 1):
        if (
            "class PipelineTask" in line
            or "PipelineTask =" in line
            or "PipelineTask(" in line
        ):
            print(
                str(path.relative_to(root)),
                "line", number,
                line.strip()[:180]
            )
            found += 1

            if found >= 12:
                break

    if found >= 12:
        break

if not found:
    print("No matching PipelineTask definitions found")

print("\n=== SHARED MODULE IMPORTS ===")

for name in (
    "typed_queue",
    "scheduler_hooks",
    "router_contract",
    "worker_lifecycle",
):
    try:
        importlib.import_module(
            "max_runtime_shared." + name
        )
        print(name.upper() + ": PASS")
    except Exception as exc:
        print(
            name.upper() + ": ERROR",
            type(exc).__name__,
            str(exc)[:250]
        )

print("\nINSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("NO MODEL OR HTTP SERVER STARTED")
print("NEXT: CORRECT REAL MAX COMPATIBILITY TEST")
PY
SH
