podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i cta-native-live /opt/venv/bin/python - <<'PY'
import urllib.request
import json

url = "http://127.0.0.1:8765/v2/cta/probe"
req = urllib.request.Request(
    url,
    data=b"{}",
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print("CTA LIVE HTTP STATUS:", r.status)
        print("CTA LIVE RESPONSE:", json.loads(r.read()))
except Exception as e:
    print("CTA LIVE HTTP ERROR:", str(e))
PY
