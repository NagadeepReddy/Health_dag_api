python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
base = json.loads((root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json").read_text())
native = json.loads(Path("/tmp/bplan_response_trace.json").read_text())

p = base["jsonData"]["prediction"]["propositionList"]
n = native["jsonData"]["prediction"]

def ids(obj):
    result = []
    if isinstance(obj, dict):
        if "propositionId" in obj:
            result.append(str(obj["propositionId"]))
        for value in obj.values():
            result.extend(ids(value))
    elif isinstance(obj, list):
        for value in obj:
            result.extend(ids(value))
    return result

expected = set(ids(p))
print("PYTORCH IDS:", sorted(expected))

for i, group in enumerate(n["ctalist"]):
    group_ids = ids(group)
    print(f"\nCTA GROUP {i}")
    if isinstance(group, dict):
        print("GROUP KEYS:", list(group))
        print("GROUP TYPE:", {k:v for k,v in group.items() if isinstance(v,(str,int,float,bool))})
    print("IDS:", group_ids)
    print("EXTRA:", sorted(set(group_ids)-expected))

print("\nSERVICE WIDGET IDS:", ids(n.get("serviceWidget", [])))
print("BPLAN BUSINESS OUTPUT GROUP INSPECTION COMPLETE")
PY
