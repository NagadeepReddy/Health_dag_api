python3 - <<'PY'
import json
from pathlib import Path

samples = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples")
expected = samples / "test_sample_myplan_bundle_output.json"
actual = Path("/tmp/bplan_myplan_trace.json")

if not expected.is_file() or not actual.is_file():
    raise SystemExit("STOP: Expected or actual response missing")

e = json.loads(expected.read_text())
a = json.loads(actual.read_text())

print("=== BPLAN MYPLAN VALIDATION ===")
print("ACTUAL KEYS:", list(a) if isinstance(a, dict) else type(a).__name__)

def business(x):
    x = x.get("jsonData", x) if isinstance(x, dict) else x
    return json.loads(x) if isinstance(x, str) else x

e, a = business(e), business(a)
diffs = []

def compare(x, y, path="$"):
    if type(x) != type(y):
        diffs.append(path + ": type mismatch")
    elif isinstance(x, dict):
        for k in x.keys() | y.keys():
            if k not in x or k not in y:
                diffs.append(path + "." + str(k) + ": missing key")
            else:
                compare(x[k], y[k], path + "." + str(k))
    elif isinstance(x, list):
        if len(x) != len(y):
            diffs.append(path + ": length mismatch")
        for i, (v, w) in enumerate(zip(x, y)):
            compare(v, w, f"{path}[{i}]")
    elif x != y:
        diffs.append(path + ": value mismatch")

compare(e, a)
print("BUSINESS OUTPUT:", "MATCH" if not diffs else "DIFFERENT")
print("DIFFERENCES:", len(diffs))
for d in diffs[:15]:
    print(d)
PY

echo "=== MAX BACKEND EXECUTION ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 300 bplan-debug 2>&1 |
  grep -E 'BPLAN REAL MAX EXECUTION|BPLAN RESPONSE ID MATCH|Traceback|RuntimeError|AttributeError' |
  tail -20
