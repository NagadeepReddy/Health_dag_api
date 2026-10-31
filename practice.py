ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== CLEAN NATIVE HTTP ==="

curl --max-time 180 -sS \
  -o "$ROOT/clean_http_final.json" \
  -w 'HTTP_STATUS:%{http_code}\n' \
  -X POST http://127.0.0.1:18767/v2/cta/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$ROOT/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

echo "=== RESPONSE ==="
python3 -B - "$ROOT/clean_http_final.json" <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    print("CTA JSON:", "FAIL" if isinstance(data,dict) and "error" in data else "PASS")
    print("PREVIEW:", str(data)[:450])
except Exception as e:
    print("CTA JSON: FAIL", e)
PY

echo "=== LATEST ERRORS ==="
$PODMAN logs --since 4m --tail 100 \
  cta-clean-native-batch2 2>&1 |
  grep -E 'FileNotFoundError|AssertionError|CTA PREDICT EXCEPTION|CTA RESPONSE' |
  tail -12
