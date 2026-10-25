podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i cta-native-live /opt/venv/bin/python - <<'PY'
import json, urllib.request
from pathlib import Path

p = Path("/workspace/artifacts/v1.167/samples/sanity_input.json")
body = json.loads(p.read_text())

req = urllib.request.Request(
    "http://127.0.0.1:8765/v2/cta/predict",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=70) as r:
        print("CTA HTTP STATUS:", r.status)
        print("CTA RESPONSE:", r.read().decode()[:1200])
except Exception as e:
    print("CTA HTTP RESULT:", type(e).__name__, str(e))
PY

echo "=== LIVE RESPONSE HANDOFF ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 250 cta-native-live 2>&1 | \
  grep -E 'LIVE RESPONSE ID|LIVE PENDING IDS|LIVE DISPATCH MATCH|CTA WORKER RESPONSE IDS: \[RequestID|Traceback|Error' | tail -12
