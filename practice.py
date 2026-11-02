ROOT=/application1/sajjna8/rt-pzai-bplan-v1

SAMPLE=$(find "$ROOT/artifacts/v1.113" "$ROOT/artifacts/v1.110" \
  -type f -name 'test_sample_1.json' -print -quit 2>/dev/null)

if [ -z "$SAMPLE" ]; then
  echo "STOP: BPLAN test sample not found"
else
  echo "TEST INPUT: $SAMPLE"

  curl -sS --max-time 500 \
    -o /tmp/bplan_native_response.json \
    -w 'BPLAN HTTP STATUS: %{http_code}\n' \
    -X POST http://127.0.0.1:18768/bplan/predict \
    -H 'Content-Type: application/json' \
    --data-binary "@$SAMPLE"

  python3 - <<'PY'
import json
from pathlib import Path

p = Path("/tmp/bplan_native_response.json")
data = json.loads(p.read_text())
print("RESPONSE TYPE:", type(data).__name__)
print("RESPONSE PREVIEW:")
print(json.dumps(data, indent=2)[:1500])
PY
fi
