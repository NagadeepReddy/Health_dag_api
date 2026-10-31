CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
SCRIPT="$CLEAN/run_cta_native.sh"

if [ -e "$SCRIPT" ]; then
  echo "STOP: Launcher already exists; not overwriting"
else
  cat > "$SCRIPT" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-check}"
NAME="${CTA_CONTAINER_NAME:-cta-clean-native-batch2}"
PORT="${CTA_PORT:-18767}"

PODMAN=(podman)
[ -z "${PODMAN_ROOT:-}" ] ||
  PODMAN+=(--root "$PODMAN_ROOT")
[ -z "${PODMAN_RUNROOT:-}" ] ||
  PODMAN+=(--runroot "$PODMAN_RUNROOT")

ART="$ROOT/artifacts/v1.168-max"
EXT="$ART/cta_native_batch2_release_candidate"

required=(
  "$ART/cta_max/sequence_weights/fn_norm1_g.npy"
  "$ART/real_max_batch2_backend.py"
  "$ART/cta_native_model"
  "$EXT/maxserve_cta_extension/cta_native_launcher.py"
  "$EXT/maxserve_cta_extension/cta_worker_adapter.py"
  "$ROOT/artifacts/v1.168/core-artifact/pipeline.py"
)

for path in "${required[@]}"; do
  if [ ! -e "$path" ]; then
    echo "STOP: Missing required artifact: $path"
    exit 1
  fi
done

echo "CLEAN PACKAGE ESSENTIAL FILES: PASS"

if [ "$ACTION" = check ]; then
  echo "LAUNCHER PREFLIGHT: PASS"
  echo "Runtime image and full dependency closure still need validation"
  exit 0
fi

if [ "$ACTION" != start ]; then
  echo "Usage: $0 check|start"
  exit 1
fi

: "${CTA_IMAGE:?STOP: Set CTA_IMAGE to an available MAX+FAISS runtime image}"

if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 18874368 ]; then
  echo "STOP: Insufficient host RAM"
  exit 1
fi

if "${PODMAN[@]}" container exists "$NAME"; then
  echo "STOP: Container name already exists: $NAME"
  exit 1
fi

"${PODMAN[@]}" image exists "$CTA_IMAGE" || {
  echo "STOP: Runtime image unavailable: $CTA_IMAGE"
  exit 1
}

exec "${PODMAN[@]}" run -d \
  --pull=never \
  --name "$NAME" \
  --memory=14g \
  --memory-swap=14g \
  --shm-size=1g \
  --cpus=4 \
  --pids-limit=256 \
  --network=bridge \
  -p "127.0.0.1:$PORT:18767" \
  --read-only \
  --tmpfs /tmp:rw,size=2g,mode=1777 \
  --workdir /workspace \
  -v "$ROOT:/workspace:ro" \
  -v "$ART/real_max_batch2_backend.py:/batch2/real_max_batch2_backend.py:ro" \
  -v "$ART/cta_max:/batch2/cta_max:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e CUDA_VISIBLE_DEVICES= \
  -e HOME=/tmp \
  -e TMPDIR=/tmp \
  -e XDG_CACHE_HOME=/tmp/cta_cache \
  -e HF_HOME=/tmp/cta_cache \
  -e TORCH_HOME=/tmp/cta_cache \
  -e OTEL_SDK_DISABLED=true \
  -e OTEL_METRICS_EXPORTER=none \
  -e OTEL_TRACES_EXPORTER=none \
  --entrypoint /opt/venv/bin/python \
  "$CTA_IMAGE" \
  -B -u -c 'from maxserve_cta_extension.cta_queue_compat import install; assert install(); from maxserve_cta_extension.cta_native_launcher import main; main()' \
  --port 18767 \
  --model-path /workspace/artifacts/v1.168-max/cta_native_model \
  --devices cpu \
  --max-batch-size 2
SH

  chmod 755 "$SCRIPT"
  bash -n "$SCRIPT" &&
    echo "CLEAN PORTABLE LAUNCHER: CREATED — SYNTAX PASS"
fi
