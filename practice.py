P="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== CONTAINER ==="
$P ps -a --filter name=cta-native-live

echo "=== HTTP READINESS ==="
$P exec cta-native-live /opt/venv/bin/python - <<'PY'
import urllib.request
try:
    req = urllib.request.Request(
        "http://127.0.0.1:8765/v2/cta/probe",
        data=b"{}",
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        print("SERVER READY:", r.status)
except Exception as e:
    print("SERVER NOT READY:", repr(e))
PY

echo "=== RECENT SERVER EVENTS ==="
$P logs --tail 30 cta-native-live 2>&1 | grep -E \
'startup complete|Uvicorn running|Shutting down|Traceback|Error|CTA CALLBACK|CTA QUEUE SIZE'
