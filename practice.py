POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
OLD=cta-batch2-importfirst-8766
NEW=cta-batch2-importfirst-8766-10g

echo "=== SAFETY ==="

[ "$("${POD[@]}" inspect "$OLD" --format '{{.State.Status}}')" = "exited" ] || {
  echo "STOP: Original test container not exited"; exit 1;
}

if "${POD[@]}" container exists "$NEW"; then
  echo "STOP: New container already exists"; exit 1
fi

python3 - <<'PY' || exit 1
from pathlib import Path
import shutil, socket

mem = next(int(x.split()[1]) for x in Path("/proc/meminfo").read_text().splitlines() if x.startswith("MemAvailable:")) / 1048576
disk = shutil.disk_usage("/application1").free / 1024**3
print(f"AVAILABLE MEMORY: {mem:.2f} GiB")
print(f"APPLICATION FREE: {disk:.2f} GiB")
assert mem >= 14 and disk >= 3, "STOP: Insufficient headroom"
with socket.socket() as s:
    assert s.connect_ex(("127.0.0.1", 8766)) != 0, "STOP: Port 8766 already occupied"
print("SAFETY: PASS")
PY

echo "=== CLONE WITH CORRECT MEMORY ==="

"${POD[@]}" container clone \
  --name "$NEW" \
  --memory 10g \
  --memory-swap 11g \
  "$OLD" || exit 1

LIMIT=$("${POD[@]}" inspect "$NEW" --format '{{.HostConfig.Memory}}')
echo "CONFIGURED LIMIT: $LIMIT"

[ "$LIMIT" = "10737418240" ] || {
  echo "STOP: 10 GiB configuration not verified"; exit 1;
}

echo "=== START ONLY NEW ISOLATED CONTAINER ==="

"${POD[@]}" start "$NEW" || exit 1

ACTUAL=$("${POD[@]}" exec "$NEW" cat /sys/fs/cgroup/memory.max 2>/dev/null) || {
  echo "STOP: Runtime memory limit cannot be verified"; exit 1;
}

echo "ACTUAL CGROUP LIMIT: $ACTUAL"

[ "$ACTUAL" = "10737418240" ] || {
  echo "STOP: Runtime memory limit incorrect"; exit 1;
}

echo "=== REAL NATIVE HTTP BATCH-2 ==="

python3 - <<'PY'
import json, time, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

base = "http://127.0.0.1:8766"
fixture = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")

ready = False
for _ in range(45):
    try:
        with urllib.request.urlopen(base + "/health", timeout=2) as r:
            ready = r.status == 200
        if ready:
            break
    except Exception:
        pass
    time.sleep(2)

print("HEALTH:", "PASS" if ready else "FAIL", flush=True)
if not ready:
    raise SystemExit("STOP: Native server not healthy")

if not fixture.is_file():
    raise SystemExit("STOP: Real CTA fixture missing")

payload = fixture.read_bytes()
json.loads(payload)
barrier = Barrier(2)

def send(n):
    barrier.wait(timeout=10)
    t = time.monotonic()
    req = urllib.request.Request(
        base + "/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            status, body = r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read().decode(errors="replace")
    except Exception as e:
        return n, False, 0, str(e), time.monotonic()-t

    try:
        result = json.loads(body)
        offers = result.get("jsonData", {}).get("prediction", {}).get("offerList")
        passed = status == 200 and isinstance(offers, list)
        detail = f"offers={len(offers)}" if passed else body[:350]
    except Exception:
        passed, detail = False, body[:350]
    return n, passed, status, detail, time.monotonic()-t

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, (1, 2)))

for n, passed, status, detail, seconds in results:
    print(f"REQUEST {n}: {'PASS' if passed else 'FAIL'} | HTTP {status} | {seconds:.2f}s | {detail}", flush=True)

print("NATIVE HTTP 2/2:", "PASS" if all(r[1] for r in results) else "FAIL")
PY

echo "=== MAX EXECUTION EVIDENCE ==="
"${POD[@]}" logs --tail 350 "$NEW" 2>&1 |
  grep -Ei 'BATCH|ENGINE_ID|EXECUT|REQUEST.ID|RESPONSE ID|RESHAPE|WORKER FAILED|OOM|TRACEBACK|ERROR' |
  tail -55

echo "=== FINAL STATE ==="
"${POD[@]}" inspect "$NEW" --format 'STATE={{.State.Status}} OOM={{.State.OOMKilled}} MEMORY={{.HostConfig.Memory}}'

echo "ORIGINAL DS/MAX: UNCHANGED"
