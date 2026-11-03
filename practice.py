python3 - <<'PY'
import json
import math
from pathlib import Path

pt_file = Path("/tmp/bplan_pytorch_final_same_request.json")
mx_file = Path("/tmp/bplan_response_trace.json")

for f in (pt_file, mx_file):
    if not f.is_file():
        raise SystemExit(f"STOP: Missing saved response: {f}")

pt = json.loads(pt_file.read_text())["jsonData"]["prediction"]
mx = json.loads(mx_file.read_text())["jsonData"]["prediction"]

print("=== BPLAN FINAL SAME-REQUEST BUSINESS PARITY ===")
print("PYTORCH KEYS:", sorted(pt))
print("NATIVE MAX KEYS:", sorted(mx))

def ids(obj):
    found = []
    if isinstance(obj, dict):
        if "propositionId" in obj:
            found.append(str(obj["propositionId"]))
        for v in obj.values():
            found.extend(ids(v))
    elif isinstance(obj, list):
        for v in obj:
            found.extend(ids(v))
    return found

for name, result in (("PYTORCH", pt), ("NATIVE MAX", mx)):
    print(f"{name} RECOMMENDATION IDS:", len(ids(result)))
    for key in ("ctalist", "serviceWidget"):
        groups = result.get(key, [])
        print(f"{name} {key} GROUPS:",
              len(groups) if isinstance(groups, list) else type(groups).__name__)

differences = []
numeric = []

def compare(a, b, path="$"):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            p = f"{path}.{key}"
            if key not in a or key not in b:
                differences.append((p, "MISSING FIELD", key in a, key in b))
            else:
                compare(a[key], b[key], p)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            differences.append((path, "LENGTH", len(a), len(b)))
        for i in range(min(len(a), len(b))):
            compare(a[i], b[i], f"{path}[{i}]")
    elif (isinstance(a, (int, float)) and not isinstance(a, bool)
          and isinstance(b, (int, float)) and not isinstance(b, bool)):
        if not math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-7):
            differences.append((path, "NUMERIC", a, b))
            numeric.append(abs(a-b))
    elif a != b:
        differences.append((path, "VALUE", str(a)[:100], str(b)[:100]))

compare(pt, mx)

print("\nPYTORCH IDS ONLY:", sorted(set(ids(pt)) - set(ids(mx))))
print("NATIVE IDS ONLY:", sorted(set(ids(mx)) - set(ids(pt))))
print("TOTAL FIELD DIFFERENCES:", len(differences))
print("MAX NUMERIC DIFFERENCE:", max(numeric, default=0))

for item in differences[:25]:
    print("DIFF:", item)

if not differences:
    print("\nBPLAN FINAL BUSINESS PARITY: PASS")
    print("READY FOR CLEAN HANDOFF")
else:
    print("\nBPLAN FINAL BUSINESS PARITY: NOT YET PASS")
    print("Resolve displayed differences before handoff")
PY
