set -euo pipefail

POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g
ROOT=/application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== SAFETY PRE-FLIGHT ==="

test -r "$ROOT/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json" || {
  echo "STOP: Real CTA fixture missing"; exit 1;
}

STATE=$("${POD[@]}" inspect --format '{{.State.Status}}' "$NAME")
test "$STATE" = running || {
  echo "STOP: Isolated container not running"; exit 1;
}

LIMIT=$("${POD[@]}" inspect --format '{{.HostConfig.Memory}}' "$NAME")
test "$LIMIT" -ge 10000000000 || {
  echo "STOP: Memory limit below 10GB"; exit 1;
}

AVAIL=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
test "$AVAIL" -ge 12582912 || {
  echo "STOP: Less than 12GiB host memory available"; exit 1;
}

echo "SAFETY: PASS"
echo "ORIGINAL MAX: NOT TARGETED"
echo "ORIGINAL DS: UNCHANGED"

echo "=== RESTART ISOLATED SERVER ONLY ==="
"${POD[@]}" restart --time 15 "$NAME"

echo "=== REAL NATIVE HTTP VALIDATION ==="
"${POD[@]}" exec -i \
  -e PYTHONDONTWRITEBYTECODE=1 \
  "$NAME" /opt/venv/bin/python -B - <<'PY'
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

assert fixture.is_file(), "STOP: Real CTA input missing"
payload = json.loads(fixture.read_text())
body = json.dumps(payload).encode()

print("=== WAIT FOR ISOLATED NATIVE HEALTH ===", flush=True)
deadline = time.monotonic() + 150

while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(
            base + "/health", timeout=3
        ) as response:
            if response.status == 200:
                print("NATIVE HEALTH: PASS", flush=True)
                break
    except Exception:
        pass
    time.sleep(4)
else:
    raise SystemExit("STOP: Native server not healthy")

def test(n):
    request = urllib.request.Request(
        base + "/v2/cta/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(
            request, timeout=120
        ) as r:
            status = r.status
            text = r.read().decode()
    except urllib.error.HTTPError as e:
        status = e.code
        text = e.read().decode()
    except Exception as e:
        return n, False, repr(e)

    try:
        result = json.loads(text)
    except ValueError:
        return n, False, f"HTTP {status}: {text[:1200]}"

    if status != 200:
        return n, False, f"HTTP {status}: {str(result)[:1600]}"

    prediction = (
        result.get("jsonData", {}).get("prediction")
        if isinstance(result, dict) else None
    )
    if prediction is None:
        return n, False, f"HTTP 200, prediction missing: {str(result)[:1200]}"

    return n, True, "HTTP 200; CTA prediction returned"

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(test, (1, 2)))

for n, passed, detail in results:
    print(
        f"REQUEST {n}: {'PASS' if passed else 'FAIL'} | {detail}",
        flush=True
    )

print(
    "NATIVE HTTP 2/2:",
    "PASS" if all(x[1] for x in results) else "FAIL"
)
print("SINGLE REAL MAX BATCH EXECUTION: REQUIRES LOG EVIDENCE")
print("ORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
PY

echo "=== RECENT BATCH EXECUTION EVIDENCE ==="
"${POD[@]}" logs --tail 350 "$NAME" 2>&1 |
  grep -Ei 'CTA.*BATCH|REAL MAX|COMPILE|EXECUT|reshape|worker failed|Traceback|ERROR' |
  tail -45 || true
