python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
actual = Path("/tmp/bplan_response_trace.json")

refs = list(root.glob("**/bplan_pytorch_baseline.json"))
refs += list(Path("/tmp").glob("bplan_pytorch_baseline.json"))

assert actual.is_file(), "HTTP response file missing"
assert refs, "Saved PyTorch baseline not found"

baseline = json.loads(refs[0].read_text())
native = json.loads(actual.read_text())

def prediction(obj):
    return obj.get("jsonData", {}).get("prediction", {})

a, b = prediction(baseline), prediction(native)

print("PYTORCH REFERENCE:", refs[0])
print("NATIVE HTTP RESPONSE:", actual)
print("PYTORCH PREDICTION KEYS:", sorted(a))
print("NATIVE PREDICTION KEYS:", sorted(b))

if not a or not b:
    print("PARITY: BLOCKED - prediction structure missing")
elif a == b:
    print("BUSINESS PARITY: EXACT PASS")
else:
    print("BUSINESS PARITY: DIFFERENCES FOUND")
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            print("DIFFERENT FIELD:", key)
            print("PYTORCH:", str(a.get(key))[:500])
            print("NATIVE:", str(b.get(key))[:500])
PY
