python3 -S -B - <<'PY'
from pathlib import Path
import json, hashlib

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
tests = root / "test-results"

max_file = tests / "cta_max_fills_response.json"
torch_file = tests / "cta_pytorch_fills_response.json"
native_file = Path("/application1/cta_queue_bridge_response.json")
native_input = root / "cta_native_adjusted_sanity_input.json"

def load(path):
    assert path.is_file(), f"STOP: Missing {path}"
    return json.loads(path.read_text())

def prediction(data):
    return data.get("jsonData", data).get("prediction", {})

def fingerprint(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]

max_pred = prediction(load(max_file))
torch_pred = prediction(load(torch_file))
native_pred = prediction(load(native_file))
current_input = load(native_input)

print("=== SAVED OUTPUT PARITY ===")
print("MAX OFFERS:", len(max_pred.get("offerList", [])))
print("PYTORCH OFFERS:", len(torch_pred.get("offerList", [])))
print("MAX VS PYTORCH:", "MATCH" if max_pred == torch_pred else "DIFFERENT")

print("\n=== NATIVE OUTPUT ===")
print("NATIVE OFFERS:", len(native_pred.get("offerList", [])))
print("NATIVE VS SAVED MAX:", "MATCH" if native_pred == max_pred else "DIFFERENT")

print("\n=== BASELINE INPUT DISCOVERY ===")
print("CURRENT INPUT:", native_input)
print("CURRENT INPUT HASH:", fingerprint(current_input))

found = 0
for p in sorted(tests.rglob("*.json")):
    if not any(s in p.name.lower() for s in ("input", "request", "sanity", "fills")):
        continue
    if p.stat().st_size > 5000000:
        continue
    try:
        data = json.loads(p.read_text())
    except (ValueError, UnicodeError):
        continue
    if not isinstance(data, dict):
        continue
    if not any(k in data for k in ("ClientFeature", "Events", "profile")):
        continue
    found += 1
    print("CANDIDATE:", p)
    print("INPUT HASH:", fingerprint(data))
    print("SAME AS NATIVE:", data == current_input)

print("INPUT CANDIDATES:", found)
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
