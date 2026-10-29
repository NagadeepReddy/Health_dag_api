python3 -S -B - <<'PY'
from pathlib import Path
import json

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
native = Path("/application1/cta_queue_bridge_response.json")

assert native.is_file(), "STOP: Native response missing"
result = json.loads(native.read_text())

def prediction(data):
    if not isinstance(data, dict):
        return None
    body = data.get("jsonData", data)
    if not isinstance(body, dict):
        return None
    value = body.get("prediction")
    return value if isinstance(value, dict) and isinstance(value.get("offerList"), list) else None

current = prediction(result)
assert current is not None, "STOP: Native CTA response contract invalid"

print("NATIVE RESPONSE: VALID")
print("NATIVE OFFER COUNT:", len(current["offerList"]))

candidates = []
for p in root.rglob("*.json"):
    if not any(word in p.name.lower() for word in
               ("response", "output", "result", "fastapi", "e2e")):
        continue
    if p.stat().st_size > 5_000_000:
        continue
    try:
        saved = json.loads(p.read_text())
    except (ValueError, UnicodeError, OSError):
        continue
    prior = prediction(saved)
    if prior is not None:
        candidates.append((p, prior))

print("SAVED BUSINESS OUTPUT BASELINES:", len(candidates))

for p, prior in candidates[:15]:
    print("BASELINE:", p)
    print("BASELINE OFFER COUNT:", len(prior["offerList"]))
    print("PREDICTION MATCH:", current == prior)

if not candidates:
    print("BUSINESS PARITY: PENDING - no saved response baseline found")
else:
    print("BUSINESS PARITY: comparison shown; confirm identical test input")

print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
