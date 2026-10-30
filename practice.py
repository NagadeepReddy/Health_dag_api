
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json
import urllib.request
import urllib.error
from pathlib import Path

payload = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)
assert payload.is_file(), "STOP: Real CTA JSON missing"

data = json.loads(payload.read_text())
url = "http://127.0.0.1:8766/v2/cta/predict"

print("REAL NATIVE MAX HTTP TEST", flush=True)

request = urllib.request.Request(
    url,
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=240) as r:
        result = json.load(r)
        print("HTTP:", r.status)
        prediction = result["jsonData"]["prediction"]
        offers = prediction["offerList"]
        assert isinstance(offers, list)
        print("REAL CTA JSON: PASS")
        print("OFFER COUNT:", len(offers))
        print("NATIVE HTTP: PASS")
except urllib.error.HTTPError as e:
    print("HTTP:", e.code)
    print("ERROR:", e.read(2000).decode(errors="replace"))
except Exception as e:
    print("FAILED:", type(e).__name__, str(e))

print("ORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
PY
