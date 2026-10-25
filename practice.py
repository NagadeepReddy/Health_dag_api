podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i cta-native-live /opt/venv/bin/python - <<'PY'
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
        print("HTTP STATUS:", r.status)
        print("RESPONSE:", r.read().decode()[:1000])
except Exception as e:
    print("HTTP RESULT:", type(e).__name__, str(e))
PY

echo "=== FINAL HANDOFF ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs cta-native-live 2>&1 | \
  grep -E 'CTA HTTP QUEUE ITEM|LIVE DISPATCH MATCH|CTA WORKER RESPONSE IDS: \[RequestID|Traceback|Error' | tail -10
