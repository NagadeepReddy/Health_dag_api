
POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g

echo "=== NETWORK MODE ==="
"${POD[@]}" inspect "$NAME" --format 'Network={{.HostConfig.NetworkMode}} Status={{.State.Status}}'

echo "=== INTERNAL MAX HEALTH ==="
"${POD[@]}" exec "$NAME" /opt/venv/bin/python -S -B -c '
import urllib.request
try:
    r = urllib.request.urlopen(
        "http://127.0.0.1:8766/health", timeout=8
    )
    print("INTERNAL HTTP:", r.status)
except Exception as e:
    print("INTERNAL ERROR:", repr(e))
'

echo "ORIGINAL MAX: UNCHANGED"
echo "NO FILES MODIFIED"
