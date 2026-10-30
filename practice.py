cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from threading import Barrier
from concurrent.futures import ThreadPoolExecutor

fixture = Path("artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
if not fixture.is_file():
    raise SystemExit("STOP: Real CTA JSON fixture missing")

payload = fixture.read_bytes()
json.loads(payload)
barrier = Barrier(2)

def test(n):
    barrier.wait(timeout=10)
    start = time.monotonic()
    request = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as r:
            status = r.status
            body = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return n, False, 0, str(e), round(time.monotonic()-start,2)

    try:
        result = json.loads(body)
        prediction = result.get("jsonData", {}).get("prediction", {})
        offers = prediction.get("offerList")
        passed = status == 200 and isinstance(offers, list)
        detail = f"offers={len(offers)}" if passed else body[:600]
    except Exception:
        passed = False
        detail = body[:600]

    return n, passed, status, detail, round(time.monotonic()-start,2)

print("=== REAL NATIVE CTA BATCH-2 ===", flush=True)

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(test, [1, 2]))

for n, passed, status, detail, elapsed in results:
    print(f"REQUEST {n}: {'PASS' if passed else 'FAIL'} | HTTP {status} | {elapsed}s | {detail}", flush=True)

print("HTTP 2/2:", "PASS" if all(x[1] for x in results) else "FAIL")
PY

echo "=== NATIVE MAX BATCH EVIDENCE ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 350 cta-batch2-importfirst-8766 2>&1 |
  grep -Ei 'BATCH|EXECUT|ENGINE_ID|REQUEST.ID|RESPONSE ID|RESHAPE|WORKER FAILED|TRACEBACK|ERROR' |
  tail -50
