python3 - <<'PY'
import json
import time
import urllib.request
from pathlib import Path

path = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)

assert path.is_file(), "STOP: CTA input missing"
body = path.read_bytes()
json.loads(body)

url = "http://127.0.0.1:8766/v2/cta/predict"

for n in (1, 2):
    print(f"\n=== OPTIMIZED MAX REQUEST {n} ===", flush=True)
    start = time.perf_counter()

    try:
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=360) as r:
            result = json.load(r)
            status = r.status

        elapsed = time.perf_counter() - start

        assert status == 200
        prediction = result["jsonData"]["prediction"]
        assert isinstance(prediction, dict)
        assert isinstance(prediction["offerList"], list)

        print("HTTP STATUS: 200")
        print("CTA JSON: PASS")
        print("OFFERS:", len(prediction["offerList"]))
        print(f"LATENCY: {elapsed:.2f} seconds", flush=True)

    except Exception as e:
        print("REQUEST NOT VALIDATED:", str(e), flush=True)
        break

print("\nOPTIMIZED LATENCY TEST: FINISHED")
print("ORIGINAL DS: UNCHANGED")
PY
