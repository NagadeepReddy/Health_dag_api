python3 - <<'PY'
import json
from pathlib import Path

files = {
    "PYTORCH": Path("/tmp/bplan_pytorch_myplan.json"),
    "MAX": Path("/tmp/bplan_myplan_trace.json"),
}

def load(p):
    obj = json.loads(p.read_text())
    data = obj["jsonData"]
    if isinstance(data, str):
        data = json.loads(data)
    return data["prediction"]["ctaList"]

pt = load(files["PYTORCH"])
mx = load(files["MAX"])

print("=== BPLAN ORDER-INDEPENDENT BUSINESS PARITY ===")

all_pass = True

for i, (a, b) in enumerate(zip(pt, mx)):
    print(f"\nLIST {i}")

    def index(items):
        out = {}
        for item in items:
            key = str(item.get("propositionId"))
            out.setdefault(key, []).append(item)
        return out

    x, y = index(a), index(b)

    print("COUNTS:", len(a), len(b))
    print("SAME IDS:", sorted(x) == sorted(y))

    differences = []

    for key in sorted(x.keys() | y.keys()):
        if key not in x or key not in y:
            differences.append((key, "missing recommendation"))
            continue

        if len(x[key]) != len(y[key]):
            differences.append((key, "duplicate count differs"))
            continue

        aa = sorted(x[key], key=lambda v: json.dumps(v, sort_keys=True))
        bb = sorted(y[key], key=lambda v: json.dumps(v, sort_keys=True))

        for left, right in zip(aa, bb):
            for field in sorted(left.keys() | right.keys()):
                if left.get(field) != right.get(field):
                    differences.append((
                        key, field,
                        left.get(field, "<MISSING>"),
                        right.get(field, "<MISSING>")
                    ))

    print("FIELD DIFFERENCES:", len(differences))
    for d in differences[:12]:
        print(" ", d)

    passed = not differences and len(a) == len(b)
    all_pass &= passed
    print("FIELDS MATCH:", passed)

print("\nORDER-INDEPENDENT BUSINESS PARITY:",
      "PASS" if all_pass else "DIFFERENT")

print("EXACT ORDER PARITY:",
      "PASS" if pt == mx else "DIFFERENT")

print("FULL NUMERICAL MODEL PARITY: NOT YET VERIFIED")
PY
