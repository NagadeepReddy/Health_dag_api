podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i cta-native-live /opt/venv/bin/python - <<'PY'
import json, urllib.request, urllib.error
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
    with urllib.request.urlopen(req, timeout=60) as r:
        print("CTA HTTP STATUS:", r.status)
        print("CTA RESPONSE:", r.read().decode()[:1200])
except urllib.error.HTTPError as e:
    print("CTA HTTP STATUS:", e.code)
    print("CTA ERROR:", e.read().decode()[:800])
except Exception as e:
    print("CTA ERROR:", type(e).__name__, str(e))
PY

echo "=== HANDOFF RESULT ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 400 cta-native-live 2>&1 | \
  grep -E 'CTA HTTP BRIDGE ENQUEUED|CTA HTTP QUEUE ITEM|LIVE DISPATCH MATCH|Traceback|Error' | tail -12
