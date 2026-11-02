python3 - <<'PY'
import json
from pathlib import Path

def load(path):
    obj = json.loads(Path(path).read_text())
    data = obj["jsonData"]
    if isinstance(data, str):
        data = json.loads(data)
    return data["prediction"]["ctaList"]

pt = load("/tmp/bplan_pytorch_myplan.json")
mx = load("/tmp/bplan_myplan_trace.json")

def canonical(items, ignore_order=False):
    cleaned = []
    for item in items:
        x = dict(item)
        if ignore_order:
            x.pop("order", None)
        cleaned.append(json.dumps(x, sort_keys=True))
    return sorted(cleaned)

print("=== BPLAN BUSINESS PARITY ===")

for i in range(max(len(pt), len(mx))):
    a = pt[i] if i < len(pt) else []
    b = mx[i] if i < len(mx) else []

    exact = canonical(a) == canonical(b)
    without_order = canonical(a, True) == canonical(b, True)

    print(f"\nLIST {i}")
    print("FULL RECORDS MATCH IGNORING POSITION:", exact)
    print("MATCH IGNORING ORDER FIELD:", without_order)

    if i == 3:
        print("\nPYTORCH PLAN RECORDS:")
        for item in a:
            print(json.dumps(item, sort_keys=True))

        print("\nMAX PLAN RECORDS:")
        for item in b:
            print(json.dumps(item, sort_keys=True))

print("\nCHECK COMPLETE — ORIGINAL FILES UNCHANGED")
PY
