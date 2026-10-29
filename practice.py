python3 -S -B - <<'PY'
from pathlib import Path
import json, hashlib

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
files = {
    "PyTorch": root / "test-results/cta_pytorch_tiles_response.json",
    "MAX": root / "test-results/cta_max_tiles_response.json",
    "Native": Path("/application1/cta_queue_bridge_response.json"),
}

def load(p):
    assert p.is_file(), f"STOP: Missing {p}"
    return json.loads(p.read_text())

def pred(data):
    body = data.get("jsonData", data)
    assert isinstance(body, dict)
    result = body.get("prediction")
    assert isinstance(result, dict)
    assert isinstance(result.get("offerList"), list)
    return result

outputs = {name: pred(load(path)) for name, path in files.items()}

print("=== BUSINESS OUTPUT COMPARISON ===")
for name, value in outputs.items():
    print(name, "OFFERS:", len(value["offerList"]))

print("PYTORCH VS MAX:",
      "MATCH" if outputs["PyTorch"] == outputs["MAX"] else "DIFFERENT")
print("NATIVE VS MAX:",
      "MATCH" if outputs["Native"] == outputs["MAX"] else "DIFFERENT")

print("\n=== INPUT IDENTIFICATION ===")
native_input = root / "cta_native_adjusted_sanity_input.json"
assert native_input.is_file()
current = load(native_input)

def fingerprint(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]

print("NATIVE INPUT SHA:", fingerprint(current))

found = 0
for p in sorted((root / "test-results").glob("*.json")):
    if not any(k in p.name.lower() for k in
               ("input", "request", "sanity")):
        continue
    if p.stat().st_size > 5000000:
        continue
    try:
        candidate = load(p)
    except (ValueError, UnicodeError):
        continue
    if isinstance(candidate, dict):
        found += 1
        print("BASELINE INPUT:", p.name)
        print("SHA:", fingerprint(candidate))
        print("SAME AS NATIVE:", candidate == current)

print("BASELINE INPUT CANDIDATES:", found)
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
