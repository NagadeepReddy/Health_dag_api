cd /application1/sajjna8/rt-pzaas-cta-offers-v1

P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P stop cta-native-live >/dev/null 2>&1 || true

$P run -d --rm --name cta-native-live \
  --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py

$P exec -i cta-native-live /opt/venv/bin/python - <<'PY'
import json, time, urllib.request
from pathlib import Path

url = "http://127.0.0.1:8765"
for _ in range(20):
    try:
        urllib.request.urlopen(
            urllib.request.Request(url + "/v2/cta/probe", data=b"{}", method="POST"),
            timeout=2
        )
        break
    except Exception:
        time.sleep(1)

body = json.loads(Path("/workspace/artifacts/v1.167/samples/sanity_input.json").read_text())
req = urllib.request.Request(
    url + "/v2/cta/predict",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print("CTA HTTP STATUS:", r.status)
        print("CTA RESPONSE:", r.read().decode()[:1000])
except Exception as e:
    print("CTA HTTP ERROR:", type(e).__name__, str(e))
PY

echo "=== CALLBACK RESULT ==="
$P logs cta-native-live 2>&1 | grep -E \
'CTA CALLBACK EXECUTED|CTA QUEUE SIZE:|CTA HTTP QUEUE ITEM|LIVE DISPATCH MATCH|Traceback|Error' | tail -12
