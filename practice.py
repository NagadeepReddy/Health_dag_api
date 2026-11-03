python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
base = json.loads((root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json").read_text())
native = json.loads(Path("/tmp/bplan_response_trace.json").read_text())

def find_ids(x):
    ids = []
    if isinstance(x, dict):
        if "propositionId" in x:
            ids.append(str(x["propositionId"]))
        for v in x.values():
            ids.extend(find_ids(v))
    elif isinstance(x, list):
        for v in x:
            ids.extend(find_ids(v))
    return ids

expected = set(find_ids(base))
prediction = native["jsonData"]["prediction"]
extras = set(find_ids(native)) - expected

print("EXTRA IDS:", sorted(extras))
print("\n=== NATIVE GROUP LOCATIONS ===")

for key, value in prediction.items():
    if isinstance(value, list):
        for i, group in enumerate(value):
            group_extra = sorted(set(find_ids(group)) & extras)
            if group_extra:
                print("GROUP:", key, "INDEX:", i)
                print("EXTRA IDS:", group_extra)
                if isinstance(group, dict):
                    print("GROUP KEYS:", list(group.keys()))
    elif isinstance(value, dict):
        group_extra = sorted(set(find_ids(value)) & extras)
        if group_extra:
            print("GROUP:", key, "EXTRA IDS:", group_extra)

print("\nEXTRA IDS ACCOUNTED FOR:",
      set(find_ids(prediction)) & extras == extras)
PY
