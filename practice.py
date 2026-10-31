python3 -B - <<'PY'
import json
import urllib.request
import urllib.error
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
source = root / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

if not source.is_file():
    raise SystemExit("STOP: Clean package input JSON missing")

request = urllib.request.Request(
    "http://127.0.0.1:18767/v2/cta/predict",
    data=source.read_bytes(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=150) as response:
        result = json.load(response)
        assert response.status == 200
        assert result not in (None, {}, [])

        print("CLEAN VM NATIVE HTTP: 200 PASS")
        print("CTA RESPONSE JSON: PASS")
        print("RESPONSE TYPE:", type(result).__name__)
        print("RESPONSE KEYS:", list(result)[:15] if isinstance(result, dict) else "Array")
except urllib.error.HTTPError as e:
    print("HTTP FAILED:", e.code)
    print(e.read(1000).decode(errors="replace"))
except Exception as e:
    print("HTTP FAILED:", type(e).__name__, str(e)[:500])
PY
