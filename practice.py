python3 -B - <<'PY'
import json
import urllib.request
import urllib.error
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
source = root / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

assert source.is_file(), "STOP: Clean CTA input missing"
payload = source.read_bytes()
json.loads(payload)

print("CLEAN NATIVE HTTP TEST: START", flush=True)

request = urllib.request.Request(
    "http://127.0.0.1:18767/v2/cta/predict",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
        if response.status != 200 or not result or (
            isinstance(result, dict) and "error" in result
        ):
            raise RuntimeError("Invalid CTA response")

        print("CLEAN NATIVE HTTP: 200 PASS")
        print("CTA JSON RESPONSE: PASS")
        print("RESPONSE TYPE:", type(result).__name__)
        print("RESPONSE KEYS:", list(result)[:15] if isinstance(result, dict) else "Array")

except urllib.error.HTTPError as e:
    print("CLEAN NATIVE HTTP: FAIL", e.code)
    print(e.read(1200).decode(errors="replace"))

except Exception as e:
    print("CLEAN NATIVE HTTP: FAIL", type(e).__name__, str(e)[:500])
PY
