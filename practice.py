python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
base = root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json"
native = Path("/tmp/bplan_response_trace.json")

a = json.loads(base.read_text())["jsonData"]["prediction"]["propositionList"]
b = json.loads(native.read_text())["jsonData"]["prediction"]["ctalist"]

def by_id(items):
    return {str(x["propositionId"]): x for x in items if isinstance(x, dict) and "propositionId" in x}

pa, pb = by_id(a), by_id(b)

print("PYTORCH:", len(a), "NATIVE:", len(b))
print("\n=== NATIVE EXTRA RECOMMENDATIONS ===")
for pid in sorted(pb.keys() - pa.keys()):
    x = pb[pid]
    print(pid, {k: x.get(k) for k in
        ("propositionName", "rank", "order", "cat", "propensity", "pplan_cd_basic", "pplan_cd_smartphone")
        if k in x})

print("\n=== COMMON RECOMMENDATION DIFFERENCES ===")
differences = 0
for pid in sorted(pa.keys() & pb.keys()):
    shared = set(pa[pid]) & set(pb[pid])
    changed = {k: (pa[pid][k], pb[pid][k])
               for k in shared if pa[pid][k] != pb[pid][k]}
    if changed:
        differences += 1
        print(pid, str(changed)[:350])

print("COMMON IDS:", len(pa.keys() & pb.keys()))
print("COMMON IDS WITH DIFFERENT SHARED FIELDS:", differences)
print("PYTORCH ONLY:", sorted(pa.keys() - pb.keys()))
print("NATIVE ONLY:", sorted(pb.keys() - pa.keys()))
PY
