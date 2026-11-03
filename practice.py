python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
files = {
    "PYTORCH": root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json",
    "NATIVE": Path("/tmp/bplan_response_trace.json"),
}

def collect(obj, path="$"):
    found = []
    if isinstance(obj, dict):
        if "propositionId" in obj:
            found.append((str(obj["propositionId"]), path, obj))
        for key, value in obj.items():
            found.extend(collect(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            found.extend(collect(value, f"{path}[{i}]"))
    return found

records = {}
for name, file in files.items():
    obj = json.loads(file.read_text())
    rows = collect(obj)
    records[name] = {pid: data for pid, path, data in rows}
    print(f"\n=== {name} ===")
    print("TOTAL RECORDS:", len(rows))
    print("UNIQUE IDS:", len(records[name]))
    print("SAMPLE PATH:", rows[0][1] if rows else "NONE")
    print("TOP-LEVEL KEYS:", list(obj) if isinstance(obj, dict) else type(obj).__name__)

a, b = records["PYTORCH"], records["NATIVE"]

print("\n=== PARITY ===")
print("COMMON IDS:", len(a.keys() & b.keys()))
print("PYTORCH ONLY:", sorted(a.keys() - b.keys()))
print("NATIVE ONLY:", sorted(b.keys() - a.keys()))

for pid in sorted(b.keys() - a.keys()):
    print("EXTRA:", pid, {
        k: b[pid].get(k)
        for k in ("propositionName", "rank", "order", "cat")
        if k in b[pid]
    })

for pid in sorted(a.keys() & b.keys()):
    changed = {
        k: (a[pid][k], b[pid][k])
        for k in a[pid].keys() & b[pid].keys()
        if a[pid][k] != b[pid][k]
    }
    if changed:
        print("SHARED FIELD DIFFERENCE:", pid, str(changed)[:300])
PY
