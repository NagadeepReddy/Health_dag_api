bash <<'SH'
set -u

ROOT=/application1
REPO=$ROOT/sajjna8/rt-pzaas-cta-offers-v1
RELEASE=$ROOT/cta_max_native_release_candidate_20261028
IMAGE=docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest
NAME=cta-final-native-smoke
LOG=$ROOT/cta_final_native_startup_20261028_v4.log

PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)

if "${PODMAN[@]}" container exists "$NAME"; then
  echo "STOP: Test container already exists"
  exit 1
fi

if [ ! -f "$RELEASE/cta_native_launcher.py" ] ||
   [ ! -d "$REPO/artifacts/v1.168-max/cta_native_model" ]; then
  echo "STOP: Native launcher or model directory missing"
  exit 1
fi

echo "NATIVE MAX STARTUP — PREVIOUSLY VERIFIED MOJO CACHE MOUNT"

timeout --signal=TERM --kill-after=10s 240s \
"${PODMAN[@]}" run --rm \
  --name "$NAME" \
  --network bridge \
  -p 127.0.0.1:18080:8000 \
  --memory 12g \
  --memory-swap 12g \
  --cpus 2 \
  --pids-limit 128 \
  --read-only \
  --tmpfs /tmp:rw,size=1g,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e TMPDIR=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace \
  -v "$REPO:/workspace:ro" \
  -v "$RELEASE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" \
  /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  --devices cpu \
  --model-path /workspace/artifacts/v1.168-max/cta_native_model \
  --port 8000 \
  >"$LOG" 2>&1

RC=$?
echo "STARTUP EXIT CODE: $RC"
echo "=== LAST STARTUP LOG ==="
tail -35 "$LOG"
echo "LOG: $LOG"
echo "ORIGINAL DS CODE: UNCHANGED"
SH
