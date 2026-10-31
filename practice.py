PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME=cta-clean-native-batch2

echo "=== CONTAINER WEIGHT PATH ==="
$PODMAN exec "$NAME" /bin/sh -c '
test -f /batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy &&
echo "DENSE WEIGHT INSIDE CONTAINER: PASS"
' || {
  echo "STOP: Weight link is not accessible inside container"
  exit 1
}

echo "=== CLEAN HTTP E2E ==="
python3 -B - <<'PY'
import json
import urllib.request
import urllib.error
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
src = root / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
assert src.is_file(), "Clean input missing"

req = urllib.request.Request(
    "http://127.0.0.1:18767/v2/cta/predict",
    data=src.read_bytes(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=120) as r:
        result = json.load(r)
        assert r.status == 200 and result
        assert not (isinstance(result, dict) and "error" in result)
        print("CLEAN NATIVE HTTP 200: PASS")
        print("CTA RESPONSE JSON: PASS")
        print("RESPONSE TYPE:", type(result).__name__)
        print("RESPONSE KEYS:", list(result)[:15] if isinstance(result, dict) else "Array")
except urllib.error.HTTPError as e:
    print("HTTP FAILED:", e.code, e.read(800).decode(errors="replace"))
except Exception as e:
    print("HTTP FAILED:", type(e).__name__, str(e)[:300])
PY
