POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g

echo "=== ISOLATED ROOTFS RECOVERY ==="

ROOTFS=$("${POD[@]}" mount "$NAME") || {
  echo "STOP: Overlay mount failed"
  exit 1
}

echo "ROOTFS: $ROOTFS"

if [ ! -d "$ROOTFS/etc" ] || [ ! -d "$ROOTFS/opt" ]; then
  echo "STOP: Container filesystem incomplete"
  "${POD[@]}" unmount "$NAME"
  exit 1
fi

echo "ROOTFS: PASS"

"${POD[@]}" unmount "$NAME" || exit 1

AVAILABLE=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)

if [ "$AVAILABLE" -lt 12582912 ]; then
  echo "STOP: Insufficient host memory"
  exit 1
fi

LIMIT=$("${POD[@]}" inspect -f '{{.HostConfig.Memory}}' "$NAME")

if [ "$LIMIT" != "10737418240" ]; then
  echo "STOP: 10 GB container limit not confirmed"
  exit 1
fi

echo "MEMORY SAFETY: PASS"

"${POD[@]}" start "$NAME" || {
  echo "STOP: Isolated container startup failed"
  exit 1
}

echo "=== REAL NATIVE CTA VALIDATION ==="

"${POD[@]}" exec -i "$NAME" /opt/venv/bin/python -B - <<'PY'
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

base = "http://127.0.0.1:8766"
fixture = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

healthy = False

for _ in range(15):
    try:
        with urllib.request.urlopen(base + "/health", timeout=3) as r:
            healthy = r.status == 200
        if healthy:
            break
    except Exception:
        time.sleep(2)

if not healthy:
    raise SystemExit("STOP: Isolated MAX not healthy")

print("ISOLATED HEALTH: PASS", flush=True)

if not fixture.is_file():
    raise SystemExit("STOP: Real CTA fixture missing")

payload = fixture.read_bytes()
json.loads(payload)

def send(n):
    req = urllib.request.Request(
        base + "/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return n, r.status, r.read(1800).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return n, e.code, e.read(1800).decode(errors="replace")
    except Exception as e:
        return n, "ERROR", repr(e)

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, (1, 2)))

for n, status, body in results:
    print(f"REQUEST {n}: HTTP {status}", flush=True)
    print(body[:1800], flush=True)

print(
    "HTTP BATCH-2:",
    "PASS" if all(x[1] == 200 for x in results) else "NOT PASSED",
    flush=True
)
PY
