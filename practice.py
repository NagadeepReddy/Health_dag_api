python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
files = {
    "PYTORCH": root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json",
    "NATIVE": Path("/tmp/bplan_response_trace.json"),
}

def records(obj, path="$"):
    out = []
    if isinstance(obj, dict):
        if "propositionId" in obj:
            out.append((path, str(obj["propositionId"]), obj))
        for k, v in obj.items():
            out.extend(records(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(records(v, f"{path}[{i}]"))
    return out

result = {}
for name, file in files.items():
    assert file.is_file(), f"Missing {name}: {file}"
    data = json.loads(file.read_text())
    rows = records(data)
    result[name] = {pid: item for _, pid, item in rows}

    print(f"\n=== {name} ===")
    print("FILE:", file)
    print("TOP LEVEL:", list(data) if isinstance(data, dict) else type(data).__name__)
    prediction = data.get("jsonData", {}).get("prediction", {}) if isinstance(data, dict) else {}
    print("PREDICTION KEYS:", list(prediction) if isinstance(prediction, dict) else type(prediction).__name__)
    print("RECORDS:", len(rows))
    print("UNIQUE IDS:", len(result[name]))
    print("SAMPLE PATHS:", [p for p, _, _ in rows[:3]])

a, b = result["PYTORCH"], result["NATIVE"]
common = set(a) & set(b)

print("\n=== BUSINESS COMPARISON ===")
print("COMMON IDS:", len(common))
print("PYTORCH ONLY:", sorted(set(a)-set(b)))
print("NATIVE ONLY:", sorted(set(b)-set(a)))

changes = []
for pid in sorted(common):
    for key in sorted(a[pid].keys() & b[pid].keys()):
        if a[pid][key] != b[pid][key]:
            changes.append((pid, key, str(a[pid][key])[:100], str(b[pid][key])[:100]))

print("SHARED FIELD DIFFERENCES:", len(changes))
for row in changes[:20]:
    print("DIFFERENCE:", row)

if not a or not b:
    print("RESULT: RESPONSE STRUCTURE NEEDS REVIEW")
elif len(a) == len(b) and set(a) == set(b) and not changes:
    print("RECOMMENDATION ID/FIELD PARITY: PASS")
else:
    print("RECOMMENDATION ID/FIELD PARITY: NOT YET PASS")
PY
