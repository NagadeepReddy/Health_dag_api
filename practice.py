bash <<'SH'
set -euo pipefail

ROOT=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
NAME=cta-stage-proof
PORT=18768

PODMAN=(podman
  --root /application1/podman/storage
  --runroot /run/containers/storage)

available=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)

if [ "$available" -lt 16777216 ]; then
  echo "STOP: Insufficient free RAM for parallel test"
  exit 0
fi

if "${PODMAN[@]}" container exists "$NAME"; then
  echo "STOP: Test container name already exists"
  exit 1
fi

created=0
passed=0

cleanup() {
  if [ "$created" = 1 ]; then
    if [ "$passed" != 1 ]; then
      "${PODMAN[@]}" logs --tail 35 "$NAME" 2>&1 || true
    fi
    "${PODMAN[@]}" rm -f "$NAME" >/dev/null 2>&1 || true
    echo "TEST CONTAINER CLEANED"
  fi
}
trap cleanup EXIT

echo "=== START ISOLATED STAGE ==="

created=1
CTA_IMAGE=cta-max-faiss:local \
CTA_CONTAINER_NAME="$NAME" \
CTA_PORT="$PORT" \
PODMAN_ROOT=/application1/podman/storage \
PODMAN_RUNROOT=/run/containers/storage \
bash "$ROOT/run_cta_native.sh" start

echo "=== INDEPENDENT HTTP TEST ==="

python3 -B - "$ROOT" "$PORT" <<'PY'
import json
import socket
import sys
import time
import urllib.request
from pathlib import Path

root = Path(sys.argv[1])
port = int(sys.argv[2])

for _ in range(90):
    try:
        with socket.create_connection(("127.0.0.1", port), 1):
            break
    except OSError:
        time.sleep(2)
else:
    raise RuntimeError("Stage server did not become ready")

src = root / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

req = urllib.request.Request(
    f"http://127.0.0.1:{port}/v2/cta/predict",
    data=src.read_bytes(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(req, timeout=240) as r:
    data = json.load(r)
    assert r.status == 200
    assert data and not (
        isinstance(data, dict) and "error" in data
    )
    print("STAGE HTTP 200: PASS")
    print("CTA JSON: PASS")
PY

passed=1
echo "ISOLATED HANDOFF RUNTIME: PASS"
SH
