
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
PACKAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106"

echo "=== SHARED MODULAR MAX INFRASTRUCTURE ==="

if [ -e "$ROOT" ]; then
  echo "STOP: Shared infra folder already exists; nothing overwritten"
  exit 1
fi

for item in \
  "$PACKAGE/model" \
  "$PACKAGE/runtime/python_deps" \
  "$PACKAGE/config/model.env"; do
  test -e "$item" || {
    echo "STOP: Required verified package item missing: $item"
    exit 1
  }
done

PODMAN=(podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage)

"${PODMAN[@]}" image exists localhost/max-shared-runtime:cpu || {
  echo "STOP: Shared MAX image alias missing"
  exit 1
}

mkdir -p "$ROOT/bin"

cat > "$ROOT/bin/run_max_model.sh" <<'LAUNCH'
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: run_max_model.sh check|start MODEL_PACKAGE"
  exit 2
fi

ACTION="$1"
PACKAGE="$2"

case "$ACTION" in
  check|start) ;;
  *) echo "STOP: Unknown action"; exit 2 ;;
esac

test -d "$PACKAGE" || {
  echo "STOP: Model package missing"
  exit 1
}

PACKAGE="$(cd "$PACKAGE" && pwd -P)"
CONFIG="$PACKAGE/config/model.env"

test -f "$CONFIG" || {
  echo "STOP: Model configuration missing"
  exit 1
}

# Trusted, locally maintained model configuration.
source "$CONFIG"

: "${MODULE:?Missing model module}"
: "${INTERNAL_PORT:?Missing internal port}"
: "${MODEL_PYTHONPATH:?Missing Python path}"

IMAGE="${MAX_IMAGE:-localhost/max-shared-runtime:cpu}"
HOST_PORT="${HOST_PORT:-18781}"
MAX_MEMORY="${MAX_MEMORY:-12g}"
MAX_PIDS="${MAX_PIDS:-512}"
PODMAN_ROOT="${PODMAN_ROOT:-/application1/podman/storage}"
PODMAN_RUNROOT="${PODMAN_RUNROOT:-/run/containers/storage}"

MODEL_DIR="$PACKAGE/model"
DEPENDENCY_DIR="$PACKAGE/runtime/python_deps"

test -d "$MODEL_DIR" || {
  echo "STOP: Model directory missing"
  exit 1
}

test -d "$DEPENDENCY_DIR" || {
  echo "STOP: Runtime dependencies missing"
  exit 1
}

[[ "$HOST_PORT" =~ ^[0-9]+$ ]] || {
  echo "STOP: Invalid host port"
  exit 1
}

[[ "$INTERNAL_PORT" =~ ^[0-9]+$ ]] || {
  echo "STOP: Invalid internal port"
  exit 1
}

PODMAN=(podman \
  --root "$PODMAN_ROOT" \
  --runroot "$PODMAN_RUNROOT")

"${PODMAN[@]}" image exists "$IMAGE" || {
  echo "STOP: Compatible MAX image not present"
  exit 1
}

echo "SHARED MAX INFRASTRUCTURE: READY"
echo "MODEL PACKAGE: $PACKAGE"
echo "MAX IMAGE: $IMAGE"
echo "MODEL ENTRYPOINT: $MODULE"
echo "HOST PORT: $HOST_PORT"
echo "INTERNAL PORT: $INTERNAL_PORT"
echo "MODEL MOUNT: READ-ONLY"
echo "DEPENDENCY MOUNT: READ-ONLY"

if [ "$ACTION" = "check" ]; then
  echo "GENERIC MAX PREFLIGHT: PASS"
  echo "NO CONTAINER STARTED"
  exit 0
fi

exec "${PODMAN[@]}" run \
  --rm --pull=never \
  --memory="$MAX_MEMORY" \
  --pids-limit="$MAX_PIDS" \
  -p "127.0.0.1:${HOST_PORT}:${INTERNAL_PORT}" \
  -v "$MODEL_DIR:/workspace:ro" \
  -v "$DEPENDENCY_DIR:/shared_deps:ro" \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e "PYTHONPATH=$MODEL_PYTHONPATH" \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" \
  -u -m "$MODULE"
LAUNCH

chmod 755 "$ROOT/bin/run_max_model.sh"

cat > "$ROOT/README.md" <<'DOC'
# Shared Modular MAX infrastructure

This is the model-independent deployment launcher.

The shared layer owns:
- Compatible MAX runtime image selection
- Container creation and resource configuration
- Read-only model and dependency mounts
- Host port mapping
- Model entrypoint execution

Each model package owns:
- Original DS code and trained weights
- MAX graph and architecture-specific adapters
- Preprocessing and postprocessing integration
- Native MAX Serve model-specific entrypoint
- Model configuration and Python import paths

The launcher does not contain model-specific Python code.

Current image alias is a development image, not an
approved production image.

This is the deployment foundation, not yet a complete
shared router/scheduler/worker implementation.
DOC

bash -n "$ROOT/bin/run_max_model.sh"

if grep -Eiq 'pzaas|bplan|cta' \
  "$ROOT/bin/run_max_model.sh"; then
  echo "STOP: Model-specific reference in generic launcher"
  exit 1
fi

if id sajjna8 >/dev/null 2>&1; then
  chown -R sajjna8:"$(id -gn sajjna8)" "$ROOT"
fi

echo "GENERIC LAUNCHER SYNTAX: PASS"
echo "MODEL-SPECIFIC CODE IN LAUNCHER: NONE"
echo "SHARED INFRA LOCATION: $ROOT"

bash "$ROOT/bin/run_max_model.sh" check "$PACKAGE"

echo "=== RESULT ==="
echo "INDEPENDENT SHARED INFRASTRUCTURE: CREATED"
echo "EXISTING HANDOFFS: UNCHANGED"
echo "EXISTING CONTAINERS: UNCHANGED"
echo "NEXT: SHARED RUNTIME INTEGRATION"
SH
