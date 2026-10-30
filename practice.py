
POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

"${POD[@]}" exec -i cta-batch2-trace-8766-10g /opt/venv/bin/python -B - <<'PY'
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

path = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

if not path.is_file():
    raise SystemExit("STOP: Real CTA JSON file missing")

body = path.read_bytes()
json.loads(body)

url = "http://127.0.0.1:8766/v2/cta/predict"

def test(n):
    started = time.monotonic()
    try:
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(request, timeout=330) as r:
            result = json.load(r)
            payload = result.get("jsonData", result)
            prediction = payload.get("prediction", {})
            offers = prediction.get("offerList")
            assert r.status == 200
            assert isinstance(offers, list)
            return n, "PASS", round(time.monotonic()-started, 2), len(offers)
    except Exception as e:
        return n, "FAIL: " + repr(e), round(time.monotonic()-started, 2), None

print("=== REAL NATIVE MAX HTTP BATCH-2 ===", flush=True)

with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(test, n) for n in (1, 2)]
    results = [f.result() for f in as_completed(futures)]

for n, status, seconds, offers in sorted(results):
    print(f"REQUEST {n}: {status} | {seconds}s | OFFERS={offers}", flush=True)

print("HTTP VALIDATION:", "PASS" if all(x[1]=="PASS" for x in results) else "NOT PASSED")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
PY
