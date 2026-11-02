SAMPLE=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json

curl -sS --max-time 180 \
  -o /tmp/bplan_typed_response.json \
  -w 'BPLAN HTTP STATUS: %{http_code}\n' \
  -X POST http://127.0.0.1:18768/bplan/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE"

python3 - <<'PY'
import json
p = "/tmp/bplan_typed_response.json"
try:
    with open(p) as f:
        data = json.load(f)
    print("RESPONSE:", json.dumps(data, indent=2)[:1500])
except Exception as e:
    print("RESPONSE ERROR:", e)
PY
