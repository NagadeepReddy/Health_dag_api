bash <<'SH'
set -euo pipefail

ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
NAME=cta-stage-proof
PORT=18768
PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)

AVAILABLE=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
if (( AVAILABLE < 16777216 )); then
  echo "STOP: Insufficient available RAM"
  exit 1
fi

if "${PODMAN[@]}" container exists "$NAME"; then
  echo "STOP: Test container already exists"
  exit 1
fi

cleanup() {
  if "${PODMAN[@]}" container exists "$NAME"; then
    "${PODMAN[@]}" logs --tail 15 "$NAME" 2>&1 || true
    "${PODMAN[@]}" rm -f "$NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "=== INDEPENDENT STAGE START ==="
CTA_IMAGE=cta-max-faiss:local \
CTA_CONTAINER_NAME="$NAME" \
CTA_PORT="$PORT" \
PODMAN_ROOT=/application1/podman/storage \
PODMAN_RUNROOT=/run/containers/storage \
bash "$ROOT/run_cta_native.sh" start

echo "=== STAGE HTTP VERIFICATION ==="
python3 -B - "$ROOT" "$PORT" <<'PY'
import sys, json, time, socket, urllib.request
from pathlib import Path

root = Path(sys.argv[1])
port = int(sys.argv[2])

for attempt in range(120):
    try:
        with socket.create_connection(("127.0.0.1", port), 2):
            break
    except OSError:
        time.sleep(2)
else:
    raise RuntimeError("Stage server startup failed")

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
    assert result and not (isinstance(result, dict) and "error" in result)
    print("STAGE HTTP 200: PASS")
    print("CTA JSON: PASS")
PY

echo "INDEPENDENT CLEAN STAGE: PASS"
SH
