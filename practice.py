
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
PACKAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106"
IMAGE="localhost/max-shared-runtime:cpu"

REL="artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_queue_compat.py"
BRIDGE="$ROOT/integrations/pzaas"
SHIM="$BRIDGE/pzaas_queue_compat.py"

echo "=== ISOLATED PZAAS SHARED QUEUE INTEGRATION ==="

test -f "$ROOT/python/max_runtime_shared/typed_queue.py"
test -f "$ROOT/bin/run_max_model_shared.sh"
test -f "$PACKAGE/model/$REL"
test -d "$PACKAGE/runtime/python_deps"
test -f "$PACKAGE/config/model.env"

if [ -e "$SHIM" ]; then
  echo "STOP: Integration adapter already exists; nothing overwritten"
  exit 1
fi

mkdir -p "$BRIDGE"

cat > "$SHIM" <<'PY'
"""PZAAS binding to model-independent MAX queue infrastructure."""

from max_runtime_shared.typed_queue import (
    install_max_typed_response_queue,
)

MAX_SHARED_QUEUE_ADAPTER_V1 = True


def install():
    from pzaas_native_serve_dev.pzaas_native_scheduler import (
        PZAASSerializableOutput,
    )

    return install_max_typed_response_queue(
        PZAASSerializableOutput,
        owner="PZAAS_v1.472",
    )
PY

python3 -B - <<'PY'
import ast
from pathlib import Path

p = Path(
    "/application1/sajjna8/max_shared_infra/"
    "integrations/pzaas/pzaas_queue_compat.py"
)

ast.parse(p.read_text())
print("SHARED QUEUE ADAPTER SYNTAX: PASS")
PY

# Trusted configuration from the verified local handoff.
source "$PACKAGE/config/model.env"

PODMAN=(
  podman
  --root /application1/podman/storage
  --runroot /run/containers/storage
)

"${PODMAN[@]}" image exists "$IMAGE" || {
  echo "STOP: Existing shared runtime image unavailable"
  exit 1
}

"${PODMAN[@]}" run \
  --rm -i --pull=never --network=none \
  --memory=4g --pids-limit=256 \
  -v "$PACKAGE/model:/workspace:ro" \
  -v "$PACKAGE/runtime/python_deps:/shared_deps:ro" \
  -v "$ROOT/python:/shared_runtime:ro" \
  -v "$SHIM:/workspace/$REL:ro" \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e "PYTHONPATH=/shared_runtime:$MODEL_PYTHONPATH" \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" -u - <<'PY'
print("=== REAL MAX SHARED QUEUE OVERLAY TEST ===")

from max.serve.scheduler.queues import (
    SchedulerZmqConfigs,
    PipelineTask,
)

from pzaas_native_serve_dev.pzaas_queue_compat import (
    MAX_SHARED_QUEUE_ADAPTER_V1,
    install,
)

assert MAX_SHARED_QUEUE_ADAPTER_V1 is True
print("ORIGINAL QUEUE MODULE: ISOLATED OVERLAY ACTIVE")

first = install()
second = install()

assert first is True
assert second is False

print("SHARED QUEUE: INSTALLED EXACTLY ONCE")
print("REPEATED INSTALL: SAFE")

marker = SchedulerZmqConfigs.__dict__.get(
    "_max_shared_queue_install"
)

assert marker is not None
assert marker[0] == "PZAAS_v1.472"

config = SchedulerZmqConfigs(
    PipelineTask.TEXT_GENERATION
)

assert config.request_queue_config is not None
assert config.response_queue_config is not None

print("REAL MAX QUEUE CONFIGURATION: PASS")
print("PZAAS RESPONSE TYPE: REGISTERED")
print("DUPLICATE HOOK PROTECTION: PASS")

print("\n=== RESULT ===")
print("ISOLATED SHARED QUEUE INTEGRATION: PASS")
print("SHARED PYTHON MODULE: ACTIVELY USED")
print("NO TRAINED MODEL LOADED")
print("NO HTTP SERVER STARTED")
print("ORIGINAL PZAAS HANDOFF: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: REAL HTTP VIA SHARED QUEUE OVERLAY")
PY

if id sajjna8 >/dev/null 2>&1; then
  chown sajjna8:"$(id -gn sajjna8)" "$SHIM"
fi
SH
