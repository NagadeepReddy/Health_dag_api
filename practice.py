python3 - <<'PY'
import json, time, urllib.request
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
assert p.is_file(), "STOP: CTA JSON missing"
body = p.read_bytes()
json.loads(body)

for n in (1, 2):
    print(f"BASELINE SEQUENTIAL REQUEST {n}: START", flush=True)
    start = time.monotonic()
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8765/v2/cta/predict",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=240) as r:
            output = json.load(r)
            status = r.status

        prediction = output["jsonData"]["prediction"]
        assert status == 200
        assert isinstance(prediction["offerList"], list)

        print(f"REQUEST {n}: PASS HTTP 200")
        print(f"LATENCY: {time.monotonic()-start:.2f}s", flush=True)
    except Exception as e:
        print(f"REQUEST {n}: NOT VERIFIED - {e}", flush=True)
        break

print("ORIGINAL DS: UNCHANGED")
PY
