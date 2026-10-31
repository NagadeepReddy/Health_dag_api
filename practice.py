python3 -B - <<'PY'
import json
import urllib.request
import urllib.error
from pathlib import Path

source = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)

assert source.is_file(), "STOP: CTA input JSON missing"
payload = source.read_bytes()
json.loads(payload)

url = "http://127.0.0.1:18767/v2/cta/predict"

print("NATIVE CTA HTTP E2E: START", flush=True)

request = urllib.request.Request(
    url,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=150) as response:
        body = response.read()
        result = json.loads(body)

        print("HTTP STATUS:", response.status)
        print("VALID JSON: PASS")
        print("RESPONSE TYPE:", type(result).__name__)
        print(
            "RESPONSE KEYS:",
            list(result)[:15] if isinstance(result, dict) else "Array"
        )
        print(
            "NATIVE CTA HTTP E2E:",
            "PASS" if response.status == 200 else "FAIL"
        )

except urllib.error.HTTPError as error:
    print("HTTP STATUS:", error.code)
    print("ERROR:", error.read(500).decode(errors="replace"))

except Exception as error:
    print("NATIVE CTA HTTP E2E: FAIL")
    print(type(error).__name__, str(error)[:400])
PY
