CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
export PODMAN_ROOT=/application1/podman/storage
export PODMAN_RUNROOT=/run/containers/storage
export CTA_IMAGE=localhost/cta-max-faiss:local

PODMAN=(podman --root "$PODMAN_ROOT" --runroot "$PODMAN_RUNROOT")

echo "=== RESTART ONLY CLEAN TEST CONTAINER ==="
"${PODMAN[@]}" stop --time 45 cta-clean-native-batch2 || exit 1
"${PODMAN[@]}" rm cta-clean-native-batch2 || exit 1

bash "$CLEAN/run_cta_native.sh" start || exit 1

echo "=== FINAL CLEAN VM HTTP E2E ==="
python3 -B - <<'PY'
import json, time, socket
import urllib.request, urllib.error
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
source = root / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

assert source.is_file(), "Missing clean CTA input JSON"
payload = source.read_bytes()
json.loads(payload)

ready = False
for _ in range(60):
    try:
        with socket.create_connection(("127.0.0.1", 18767), timeout=2):
            ready = True
            break
    except OSError:
        time.sleep(2)

if not ready:
    raise SystemExit("FAIL: Clean MAX server did not become ready")

request = urllib.request.Request(
    "http://127.0.0.1:18767/v2/cta/predict",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=150) as response:
        result = json.load(response)
        assert response.status == 200
        assert result not in (None, {}, [])
        assert not (isinstance(result, dict) and "error" in result)
        print("CLEAN VM HTTP 200: PASS")
        print("CTA VALID JSON: PASS")
        print("RESPONSE TYPE:", type(result).__name__)
        print("RESPONSE KEYS:", list(result)[:15] if isinstance(result, dict) else "Array")
except urllib.error.HTTPError as e:
    print("CLEAN VM HTTP: FAIL", e.code)
    print(e.read(1200).decode(errors="replace"))
except Exception as e:
    print("CLEAN VM HTTP: FAIL", type(e).__name__, str(e)[:500])
PY
