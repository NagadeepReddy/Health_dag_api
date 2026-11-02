python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter

def load(path):
    obj = json.loads(Path(path).read_text())
    data = obj["jsonData"]
    if isinstance(data, str):
        data = json.loads(data)
    return data["prediction"]["ctaList"]

pt = load("/tmp/bplan_pytorch_myplan.json")
mx = load("/tmp/bplan_myplan_trace.json")

print("=== LIST 3: MATCH BY PLAN NAME ===")

def by_name(items):
    return {x.get("propositionName"): x for x in items}

a = by_name(pt[3])
b = by_name(mx[3])

for name in sorted(a.keys() | b.keys(), key=str):
    print("\nPLAN:", name)
    left = a.get(name, {})
    right = b.get(name, {})
    for field in sorted(left.keys() | right.keys()):
        if left.get(field) != right.get(field):
            print("FIELD:", field)
            print(" PYTORCH:", left.get(field, "<MISSING>"))
            print(" MAX:    ", right.get(field, "<MISSING>"))

print("\n=== IGNORE POSITION AND ORDER FIELD ===")

for i, (left, right) in enumerate(zip(pt, mx)):
    def normalize(items):
        records = []
        for item in items:
            x = dict(item)
            x.pop("order", None)
            records.append(json.dumps(x, sort_keys=True))
        return Counter(records)

    missing = normalize(left) - normalize(right)
    extra = normalize(right) - normalize(left)

    print(f"LIST {i}:",
          "PASS" if not missing and not extra else "DIFFERENT")
    if missing:
        print(" PYTORCH ONLY:", list(missing)[:3])
    if extra:
        print(" MAX ONLY:", list(extra)[:3])
PY
