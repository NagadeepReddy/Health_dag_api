python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
a = json.loads((root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json").read_text())
b = json.loads(Path("/tmp/bplan_native_response.json").read_text())

def extract(x):
    x = x.get("jsonData", x)
    x = x.get("prediction", x)
    return x["ctaList"]

a, b = extract(a), extract(b)

print("=== BPLAN FINAL BUSINESS PARITY ===")
for i, (left, right) in enumerate(zip(a, b)):
    la = {str(x.get("propositionId", x.get("propositionName"))): x for x in left}
    lb = {str(x.get("propositionId", x.get("propositionName"))): x for x in right}
    common = la.keys() & lb.keys()
    diffs = [
        (k, field, la[k].get(field), lb[k].get(field))
        for k in common
        for field in la[k].keys() | lb[k].keys()
        if la[k].get(field) != lb[k].get(field)
    ]
    print(f"LIST {i}: counts={len(left)}/{len(right)} IDs_match={la.keys()==lb.keys()} field_differences={len(diffs)}")
    for item in diffs[:8]:
        print(" ", item)

print("EXACT BUSINESS PARITY:", "PASS" if a == b else "FAIL")
PY
