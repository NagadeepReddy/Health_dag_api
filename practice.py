python3 -S -B - <<'PY'
import json, time, socket
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

host, port = "127.0.0.1", 18080
url = f"http://{host}:{port}/v2/cta/predict"

try:
    with socket.create_connection((host, port), timeout=3):
        pass
except OSError:
    print("LIVE MAX SERVER: NOT LISTENING")
    print("STOP: Standalone startup still required")
    raise SystemExit(0)

p = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)
assert p.is_file(), "STOP: Real CTA input missing"
body = json.loads(p.read_text())

print("REAL CTA INPUT: LOADED")
print("NATIVE HTTP REQUEST: START")

start = time.monotonic()
req = Request(
    url,
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urlopen(req, timeout=300) as r:
        status = r.status
        result = json.load(r)
except HTTPError as e:
    print("HTTP STATUS:", e.code)
    print("ERROR:", e.read(1000).decode(errors="replace"))
    raise SystemExit(1)

print("HTTP STATUS:", status)
print("LATENCY SECONDS:", round(time.monotonic()-start, 3))
print("RESPONSE:", json.dumps(result)[:1500])

assert status == 200
assert isinstance(result, dict)
assert "jsonData" in result
print("REAL NATIVE HTTP: PASS")
print("FILES MODIFIED: NONE")
PY
