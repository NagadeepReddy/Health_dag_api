bash <<'SH'
set -Eeuo pipefail

ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
MAIN=cta-clean-native-batch2
TEST=cta-stage-proof
PORT=18768
PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)

[ "$("${PODMAN[@]}" inspect "$MAIN" --format '{{.State.Running}}')" = true ] || {
  echo "STOP: Original container is not running"
  exit 1
}

if "${PODMAN[@]}" container exists "$TEST"; then
  echo "STOP: Test container already exists"
  exit 1
fi

restore=0
passed=0

cleanup() {
  status=$?
  trap - EXIT

  if "${PODMAN[@]}" container exists "$TEST"; then
    if [ "$passed" = 0 ]; then
      echo "=== STAGE FAILURE LOGS ==="
      "${PODMAN[@]}" logs --tail 35 "$TEST" 2>&1 || true
    fi
    "${PODMAN[@]}" rm -f "$TEST" >/dev/null 2>&1 || true
  fi

  if [ "$restore" = 1 ]; then
    echo "=== RESTORE ORIGINAL ==="
    if [ "$("${PODMAN[@]}" inspect "$MAIN" --format '{{.State.Running}}' 2>/dev/null)" != true ]; then
      "${PODMAN[@]}" start "$MAIN" >/dev/null || {
        echo "ALERT: ORIGINAL RESTART FAILED"
        exit 1
      }
    fi
    echo "ORIGINAL CONTAINER RESTORED: PASS"
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "=== TEMPORARILY STOP ORIGINAL ==="
restore=1
"${PODMAN[@]}" stop --time 30 "$MAIN" >/dev/null

available=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
echo "AVAILABLE RAM KiB: $available"

if (( available < 18874368 )); then
  echo "STOP: Still below launcher RAM requirement"
  exit 1
fi

echo "=== START INDEPENDENT STAGE ==="
CTA_IMAGE=cta-max-faiss:local \
CTA_CONTAINER_NAME="$TEST" \
CTA_PORT="$PORT" \
PODMAN_ROOT=/application1/podman/storage \
PODMAN_RUNROOT=/run/containers/storage \
bash "$ROOT/run_cta_native.sh" start

echo "=== VERIFY NATIVE HTTP ==="
python3 -B - "$ROOT" "$PORT" <<'PY'
import json, sys, time, socket, urllib.request
from pathlib import Path

root = Path(sys.argv[1])
port = int(sys.argv[2])

for _ in range(120):
    try:
        with socket.create_connection(("127.0.0.1", port), 2):
            break
    except OSError:
        time.sleep(2)
else:
    raise RuntimeError("Server failed to start")

src = root / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
req = urllib.request.Request(
    f"http://127.0.0.1:{port}/v2/cta/predict",
    data=src.read_bytes(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(req, timeout=240) as response:
    result = json.load(response)
    assert response.status == 200
    assert result and not (
        isinstance(result, dict) and "error" in result
    )
    print("STAGE NATIVE HTTP 200: PASS")
    print("STAGE CTA JSON: PASS")
PY

passed=1
echo "INDEPENDENT HANDOFF TEST: PASS"
SH
