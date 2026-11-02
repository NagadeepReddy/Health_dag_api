ROOT=/application1/sajjna8/rt-pzai-bplan-v1
SAMPLES="$ROOT/artifacts/v1.113/core-artifact/test_samples"
INPUT="$SAMPLES/test_sample_myplan_bundle.json"
EXPECTED="$SAMPLES/test_sample_myplan_bundle_output.json"
ACTUAL=/tmp/bplan_bundle_max_result.json

test -f "$INPUT" && test -f "$EXPECTED" || { echo "STOP: Test files missing"; exit 1; }

echo "=== BPLAN MAX BUSINESS OUTPUT TEST ==="
curl -sS --max-time 180 \
  -X POST http://127.0.0.1:18768/bplan/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$INPUT" \
  -o "$ACTUAL" \
  -w 'HTTP STATUS: %{http_code}\nTIME: %{time_total}s\n'

echo "=== EXPECTED VS MAX RESPONSE ==="
python3 - "$EXPECTED" "$ACTUAL" <<'PY'
import json, sys
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text())

expected = load(sys.argv[1])
actual = load(sys.argv[2])

def business(obj):
    data = obj.get("jsonData", obj)
    if isinstance(data, str):
        return json.loads(data)
    return data

e = business(expected)
a = business(actual)

differences = []

def compare(x, y, path="$"):
    if type(x) is not type(y):
        differences.append(path + ": type differs")
    elif isinstance(x, dict):
        for key in sorted(x.keys() | y.keys()):
            if key not in x or key not in y:
                differences.append(path + "." + key + ": missing key")
            else:
                compare(x[key], y[key], path + "." + key)
    elif isinstance(x, list):
        if len(x) != len(y):
            differences.append(path + ": list length differs")
        for i, (v1, v2) in enumerate(zip(x, y)):
            compare(v1, v2, f"{path}[{i}]")
    elif x != y:
        differences.append(path + ": value differs")

compare(e, a)

print("EXPECTED TYPE:", type(e).__name__)
print("MAX TYPE:", type(a).__name__)
print("BUSINESS OUTPUT:", "MATCH" if not differences else "DIFFERENT")
print("DIFFERENCE COUNT:", len(differences))
for difference in differences[:10]:
    print(" -", difference)
PY
