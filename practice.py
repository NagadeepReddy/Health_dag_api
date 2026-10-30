sudo bash -s <<'BASH'
set -euo pipefail

POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g

echo "=== ISOLATED STORAGE RECOVERY ==="

STATE=$("${POD[@]}" inspect --format '{{.State.Status}}' "$NAME")
echo "STATE: $STATE"

LIMIT=$("${POD[@]}" inspect --format '{{.HostConfig.Memory}}' "$NAME")
test "$LIMIT" -ge 10000000000 || {
  echo "STOP: 10GB limit missing"; exit 1;
}

if [ "$STATE" != running ]; then
  case "$STATE" in
    exited|stopped|created|configured) ;;
    *) echo "STOP: Unexpected container state"; exit 1 ;;
  esac

  "${POD[@]}" container cleanup "$NAME"

  MOUNT=$("${POD[@]}" mount "$NAME")
  echo "MOUNT: $MOUNT"

  case "$MOUNT" in
    /application1/podman/storage/overlay/*/merged) ;;
    *) echo "STOP: Unexpected mount"; exit 1 ;;
  esac

  test -f "$MOUNT/etc/passwd" || {
    echo "STOP: Container image /etc/passwd missing"
    exit 1
  }

  echo "OVERLAY: VERIFIED"

  AVAILABLE=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
  test "$AVAILABLE" -ge 12582912 || {
    echo "STOP: Insufficient available host memory"
    exit 1
  }

  "${POD[@]}" start "$NAME"
fi

echo "=== REAL NATIVE BATCH-2 HTTP ==="

HTTP_RC=0
"${POD[@]}" exec -i \
  -e PYTHONDONTWRITEBYTECODE=1 \
  "$NAME" /opt/venv/bin/python -B - <<'PY' || HTTP_RC=$?
import json, time, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

base = "http://127.0.0.1:8766"
path = Path("/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
assert path.is_file(), "Real CTA input missing"
body = json.dumps(json.loads(path.read_text())).encode()

healthy = False
for _ in range(30):
    try:
        with urllib.request.urlopen(base + "/health", timeout=3) as r:
            if r.status == 200:
                healthy = True
                break
    except Exception:
        time.sleep(3)

if not healthy:
    raise SystemExit("STOP: Isolated server unhealthy")

print("HEALTH: PASS", flush=True)

def request(n):
    req = urllib.request.Request(
        base + "/v2/cta/predict",
        data=body,
        headers={"Content-Type":"application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status = r.status
            output = json.loads(r.read())
        prediction = output.get("jsonData", {}).get("prediction")
        return n, status == 200 and prediction is not None, str(output)[:350]
    except Exception as e:
        return n, False, str(e)[:350]

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(request, [1, 2]))

for n, passed, detail in results:
    print(f"REQUEST {n}: {'PASS' if passed else 'FAIL'} | {detail}", flush=True)

print("NATIVE HTTP BATCH-2:", "PASS" if all(x[1] for x in results) else "FAIL")
if not all(x[1] for x in results):
    raise SystemExit(1)
PY

echo "=== MAX EXECUTION EVIDENCE ==="
"${POD[@]}" logs --tail 450 "$NAME" 2>&1 |
  grep -Ei 'BATCH|REAL MAX|COMPILE|EXECUT|reshape|worker failed|Traceback|ERROR' |
  tail -50 || true

echo "ORIGINAL DS: UNCHANGED"
echo "ORIGINAL MAX: NOT TARGETED"
echo "ISOLATED HTTP EXIT: $HTTP_RC"
exit "$HTTP_RC"
BASH
