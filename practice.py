retry_cta_batch2() {
  local NAME=cta-batch2-importfirst-8766
  local POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

  echo "=== SAFETY PRE-FLIGHT ==="

  local STATE
  STATE=$("${POD[@]}" inspect "$NAME" --format '{{.State.Status}}') || return 1

  if [ "$STATE" != "exited" ]; then
    echo "STOP: Expected exited container; found $STATE"
    return 1
  fi

  python3 - <<'PY'
from pathlib import Path
import shutil, sys

info = {}
for line in Path("/proc/meminfo").read_text().splitlines():
    k, _, v = line.partition(":")
    if k == "MemAvailable":
        info[k] = int(v.strip().split()[0]) * 1024

gib = 1024**3
available = info["MemAvailable"] / gib
disk = shutil.disk_usage("/application1").free / gib

print(f"HOST AVAILABLE: {available:.2f} GiB")
print(f"APPLICATION1 FREE: {disk:.2f} GiB")

if available < 14 or disk < 3:
    sys.exit("STOP: Insufficient host headroom")

print("SAFETY: PASS")
PY
  [ $? -eq 0 ] || return 1

  echo "=== UPDATE EXISTING ISOLATED CONTAINER ==="

  "${POD[@]}" update \
    --memory 10g \
    --memory-swap 11g \
    "$NAME" || return 1

  local LIMIT
  LIMIT=$("${POD[@]}" inspect "$NAME" --format '{{.HostConfig.Memory}}') || return 1

  if [ "$LIMIT" != "10737418240" ]; then
    echo "STOP: 10 GiB limit not verified: $LIMIT"
    return 1
  fi

  echo "MEMORY LIMIT: VERIFIED 10 GiB"

  "${POD[@]}" start "$NAME" || return 1

  echo "=== REAL NATIVE BATCH-2 VALIDATION ==="

  python3 - <<'PY'
import json, time, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

url = "http://127.0.0.1:8766"
fixture = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)

ready = False
for _ in range(45):
    try:
        with urllib.request.urlopen(url + "/health", timeout=2) as r:
            ready = r.status == 200
        if ready:
            break
    except Exception:
        pass
    time.sleep(2)

print("NATIVE HEALTH:", "PASS" if ready else "FAIL", flush=True)

if not ready:
    print("STOP: No HTTP requests sent")
    raise SystemExit(0)

if not fixture.is_file():
    print("STOP: Real CTA fixture missing")
    raise SystemExit(0)

payload = fixture.read_bytes()
json.loads(payload)
barrier = Barrier(2)

def send(n):
    barrier.wait(timeout=10)
    start = time.monotonic()
    req = urllib.request.Request(
        url + "/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            status = r.status
            body = r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode(errors="replace")
    except Exception as e:
        return n, False, 0, repr(e), time.monotonic()-start

    try:
        data = json.loads(body)
        pred = data.get("jsonData", {}).get("prediction", {})
        offers = pred.get("offerList")
        passed = status == 200 and isinstance(offers, list)
        detail = f"offers={len(offers)}" if passed else body[:500]
    except Exception:
        passed = False
        detail = body[:500]

    return n, passed, status, detail, time.monotonic()-start

with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(send, (1, 2)))

for n, passed, status, detail, elapsed in results:
    print(
        f"REQUEST {n}: {'PASS' if passed else 'FAIL'} "
        f"| HTTP {status} | {elapsed:.2f}s | {detail}",
        flush=True
    )

print("NATIVE HTTP 2/2:",
      "PASS" if all(x[1] for x in results) else "FAIL")
PY

  echo "=== FINAL BATCH EXECUTION EVIDENCE ==="

  "${POD[@]}" logs --tail 250 "$NAME" 2>&1 |
    grep -Ei 'BATCH|ENGINE_ID|EXECUT|REQUEST.ID|RESPONSE ID|RESHAPE|WORKER FAILED|OOM|TRACEBACK|ERROR' |
    tail -45

  echo "=== FINAL CONTAINER STATE ==="
  "${POD[@]}" inspect "$NAME" --format \
    'STATE={{.State.Status}} OOM={{.State.OOMKilled}} MEMORY={{.HostConfig.Memory}}'

  echo "ORIGINAL DS/MAX: NOT MODIFIED"
}

retry_cta_batch2
