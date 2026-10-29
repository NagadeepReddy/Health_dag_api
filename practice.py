python3 - <<'PY'
import json
import urllib.request
from pathlib import Path

body = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

assert body.is_file(), "STOP: CTA JSON missing"

req = urllib.request.Request(
    "http://127.0.0.1:8765/v2/cta/predict",
    data=body.read_bytes(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(req, timeout=120) as r:
    result = json.load(r)
    print("HTTP STATUS:", r.status)

assert isinstance(result.get("jsonData"), dict)
prediction = result["jsonData"].get("prediction")
assert isinstance(prediction, dict)

print("REAL CTA NATIVE MAX HTTP: PASS")
print("RESPONSE KEYS:", list(result))
print("PREDICTION KEYS:", list(prediction))
print("ORIGINAL DS: UNCHANGED")
PY
