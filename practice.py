cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i cta-native-live /opt/venv/bin/python - <<'PY'
import json
import urllib.request
import urllib.error
from pathlib import Path

files = sorted(Path("/workspace").rglob("sanity_input.json"))
if not files:
    print("REAL CTA INPUT: NOT FOUND")
    raise SystemExit(1)

p = files[0]
body = json.loads(p.read_text())
print("CTA INPUT:", str(p), flush=True)
print("CTA INPUT TYPE:", type(body).__name__, flush=True)

if not isinstance(body, dict):
    print("CTA INPUT MUST BE A JSON OBJECT")
    raise SystemExit(1)

req = urllib.request.Request(
    "http://127.0.0.1:8765/v2/cta/predict",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=125) as r:
        result = json.loads(r.read())
        print("CTA NATIVE HTTP STATUS:", r.status)
        print("CTA RESPONSE:", json.dumps(result)[:1500])
except urllib.error.HTTPError as e:
    print("CTA NATIVE HTTP STATUS:", e.code)
    print("CTA ERROR:", e.read().decode()[:1000])
except Exception as e:
    print("CTA ERROR:", type(e).__name__, str(e))
PY
