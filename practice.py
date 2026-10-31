ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

curl --max-time 180 -sS \
  -o "$ROOT/clean_http_verified.json" \
  -w 'HTTP_STATUS:%{http_code}\n' \
  -X POST http://127.0.0.1:18767/v2/cta/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$ROOT/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

echo "=== CTA RESPONSE ==="
python3 -B - "$ROOT/clean_http_verified.json" <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    print("RESPONSE TYPE:", type(data).__name__)
    print("RESPONSE PREVIEW:", str(data)[:500])
    print("CTA JSON:", "FAIL" if isinstance(data, dict) and "error" in data else "PASS")
except Exception as e:
    print("CTA JSON: FAIL:", e)
PY
