python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
baseline = root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json"
native = Path("/tmp/bplan_response_trace.json")

assert baseline.is_file(), f"Missing baseline: {baseline}"
assert native.is_file(), f"Missing native response: {native}"

a = json.loads(baseline.read_text())
b = json.loads(native.read_text())

def collect(obj):
    found = []
    def walk(x):
        if isinstance(x, dict):
            if "propositionId" in x:
                found.append(str(x["propositionId"]))
            for value in x.values():
                walk(value)
        elif isinstance(x, list):
            for value in x:
                walk(value)
    walk(obj)
    return found

pa, pb = collect(a), collect(b)

print("PYTORCH RECOMMENDATIONS:", len(pa))
print("NATIVE RECOMMENDATIONS:", len(pb))
print("SAME IDS:", sorted(pa) == sorted(pb))
print("SAME ORDER:", pa == pb)
print("PYTORCH ONLY:", sorted(set(pa)-set(pb))[:30])
print("NATIVE ONLY:", sorted(set(pb)-set(pa))[:30])

if not pa or not pb:
    print("RESULT: BLOCKED — need correct business ID mapping")
elif pa == pb:
    print("ID AND ORDER PARITY: PASS")
elif sorted(pa) == sorted(pb):
    print("ID PARITY: PASS; ORDER DIFFERS")
else:
    print("BUSINESS ID PARITY: DIFFERENT")
PY
