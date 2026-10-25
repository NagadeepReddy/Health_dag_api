P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P exec -i cta-native-live /opt/venv/bin/python - <<'PY'
import json, urllib.request
from pathlib import Path

body = json.loads(Path(
    "/workspace/artifacts/v1.167/samples/sanity_input.json"
).read_text())

req = urllib.request.Request(
    "http://127.0.0.1:8765/v2/cta/predict",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=45) as r:
        print("CTA HTTP STATUS:", r.status)
        print("CTA RESPONSE:", r.read().decode()[:1000])
except Exception as e:
    print("CTA HTTP ERROR:", type(e).__name__, str(e))
PY

echo "=== RESPONSE DELIVERY ==="
$P logs cta-native-live 2>&1 | grep -E \
'CTA CALLBACK EXECUTED|CTA QUEUE SIZE:|CTA HTTP QUEUE ITEM|LIVE DISPATCH MATCH|Traceback|Error' | tail -12
