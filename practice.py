P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P exec -i cta-native-live /opt/venv/bin/python - <<'PY'
import json, time, urllib.request
from pathlib import Path

base = "http://127.0.0.1:8765"

for i in range(40):
    try:
        req = urllib.request.Request(
            base + "/v2/cta/probe", data=b"{}", method="POST"
        )
        with urllib.request.urlopen(req, timeout=2):
            print("SERVER READY: YES", flush=True)
        break
    except Exception:
        time.sleep(1)
else:
    print("SERVER READY: NO")
    raise SystemExit(1)

body = json.loads(Path(
    "/workspace/artifacts/v1.167/samples/sanity_input.json"
).read_text())

req = urllib.request.Request(
    base + "/v2/cta/predict",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=45) as r:
        print("CTA HTTP STATUS:", r.status)
        print("CTA RESPONSE:", r.read().decode()[:1200])
except Exception as e:
    print("CTA HTTP ERROR:", type(e).__name__, str(e))
PY

echo "=== RESPONSE WORKER RESULT ==="
$P logs cta-native-live 2>&1 | grep -E \
'CTA_RESPONSE_WORKER_STARTED|CTA HTTP QUEUE ITEM|LIVE DISPATCH MATCH|CTA WORKER RESPONSE IDS: \[RequestID|Traceback|Error' | tail -12
