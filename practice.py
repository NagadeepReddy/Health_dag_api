POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-importfirst-8766-10g

echo "=== SAFETY AND NETWORK ==="
"${POD[@]}" inspect "$NAME" --format \
'STATE={{.State.Status}} OOM={{.State.OOMKilled}} MEMORY={{.HostConfig.Memory}} NETWORK={{.HostConfig.NetworkMode}}'

STATE=$("${POD[@]}" inspect "$NAME" --format '{{.State.Status}}') || exit 1
[ "$STATE" = "running" ] || { echo "STOP: Container not running"; exit 1; }

LIMIT=$("${POD[@]}" exec "$NAME" cat /sys/fs/cgroup/memory.max) || exit 1
[ "$LIMIT" = "10737418240" ] || { echo "STOP: 10 GiB limit missing"; exit 1; }

echo "=== INTERNAL HEALTH AND TWO REAL CTA REQUESTS ==="

"${POD[@]}" exec -i -e PYTHONDONTWRITEBYTECODE=1 "$NAME" \
  /opt/venv/bin/python -B - <<'PY'
import json, time, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

base = "http://127.0.0.1:8766"

try:
    with urllib.request.urlopen(base + "/health", timeout=6) as r:
        print("INTERNAL HEALTH:", r.status, flush=True)
        assert r.status == 200
except Exception as e:
    print("STOP: Internal health failed:", repr(e), flush=True)
    raise SystemExit(2)

fixture = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

if not fixture.is_file():
    raise SystemExit("STOP: Real CTA fixture missing")

payload = fixture.read_bytes()
json.loads(payload)

barrier = Barrier(2)

def send(n):
    barrier.wait(timeout=10)
    start = time.monotonic()
    req = urllib.request.Request(
        base + "/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status = r.status
            body = r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode(errors="replace")
    except Exception as e:
        return n, False, 0, repr(e), time.monotonic()-start

    try:
        data = json.loads(body)
        offers = data.get("jsonData", {}).get(
            "prediction", {}
        ).get("offerList")

        passed = status == 200 and isinstance(offers, list)
        detail = (
            f"offers={len(offers)}"
            if passed else str(data)[:500]
        )
    except Exception:
        passed = False
        detail = body[:500]

    return n, passed, status, detail, time.monotonic()-start

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, (1, 2)))

for n, passed, status, detail, elapsed in results:
    print(
        f"REQUEST {n}: {'PASS' if passed else 'FAIL'} "
        f"| HTTP {status} | {elapsed:.2f}s | {detail}",
        flush=True
    )

print(
    "REAL CTA HTTP 2/2:",
    "PASS" if all(x[1] for x in results) else "FAIL",
    flush=True
)
PY

echo "=== ACTUAL MAX EXECUTION LOGS ==="
"${POD[@]}" logs --tail 650 "$NAME" 2>&1 |
  grep -Ei 'ENGINE_ID|BATCH|EXECUT|RESHAPE|RESPONSE ID|REQUEST.ID|WORKER FAILED|OOM|TRACEBACK|ERROR' |
  tail -70

echo "=== FINAL STATUS ==="
"${POD[@]}" inspect "$NAME" --format \
'STATE={{.State.Status}} OOM={{.State.OOMKilled}}'
