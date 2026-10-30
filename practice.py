python3 -B - <<'PY'
import json
import urllib.request
from pathlib import Path

body = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

assert body.is_file(), "STOP: CTA request missing"
payload = json.loads(body.read_text())
assert isinstance(payload, dict)

req = urllib.request.Request(
    "http://127.0.0.1:8765/v2/cta/predict",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)

print("NATIVE MAX SINGLE CTA REQUEST: START", flush=True)

with opener.open(req, timeout=240) as r:
    result = json.load(r)
    print("HTTP STATUS:", r.status, flush=True)
    assert r.status == 200

assert isinstance(result, dict)
assert isinstance(result.get("jsonData"), dict)
assert isinstance(result["jsonData"].get("prediction"), dict)

print("NATIVE MAX SINGLE CTA HTTP: PASS")
print("RESPONSE KEYS:", list(result))
print("PREDICTION KEYS:", list(result["jsonData"]["prediction"]))
print("ORIGINAL DS: UNCHANGED")
PY
