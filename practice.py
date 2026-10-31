python3 -B - <<'PY'
from pathlib import Path
import urllib.request
import urllib.error
import json

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
src = root / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

req = urllib.request.Request(
    "http://127.0.0.1:18767/v2/cta/predict",
    data=src.read_bytes(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=180) as r:
        result = json.load(r)
        print("HTTP_STATUS:", r.status)
        print("CTA RESPONSE:", str(result)[:600])
        print("CLEAN HTTP:", "PASS" if r.status == 200 and result and not (isinstance(result, dict) and "error" in result) else "FAIL")
except urllib.error.HTTPError as e:
    print("HTTP_STATUS:", e.code)
    print("ERROR:", e.read(800).decode(errors="replace"))
except Exception as e:
    print("CLEAN HTTP: FAIL", type(e).__name__, str(e))
PY
