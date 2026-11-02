python3 - <<'PY'
import json
from pathlib import Path

pt_path = Path("/tmp/bplan_pytorch_myplan.json")
mx_path = Path("/tmp/bplan_myplan_trace.json")

if not pt_path.is_file() or not mx_path.is_file():
    raise SystemExit("STOP: Existing PyTorch or MAX response missing")

def load(path):
    obj = json.loads(path.read_text())
    data = obj["jsonData"]
    if isinstance(data, str):
        data = json.loads(data)
    return obj, data["prediction"]["ctaList"]

pt_obj, pt = load(pt_path)
mx_obj, mx = load(mx_path)

print("=== LIST 1 ORDER ===")
for label, groups in (("PYTORCH", pt), ("MAX", mx)):
    print(label, [
        str(x.get("propositionId"))
        for x in groups[1]
    ])

print("\n=== EXACT BUSINESS DIFFERENCES ===")
diffs = []

def compare(a, b, path="$"):
    if type(a) is not type(b):
        diffs.append((path, a, b))
    elif isinstance(a, dict):
        for key in sorted(a.keys() | b.keys()):
            if key not in a or key not in b:
                diffs.append((path+"."+str(key),
                              a.get(key, "<MISSING>"),
                              b.get(key, "<MISSING>")))
            else:
                compare(a[key], b[key], path+"."+str(key))
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append((path+".length", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, f"{path}[{i}]")
    elif a != b:
        diffs.append((path, a, b))

compare(pt, mx)

print("DIFFERENCES:", len(diffs))
for path, a, b in diffs[:25]:
    print("FIELD:", path)
    print("  PYTORCH:", str(a)[:150])
    print("  MAX:    ", str(b)[:150])

print("\n=== INFERENCE METADATA ===")
for label, obj in (("PYTORCH", pt_obj), ("MAX", mx_obj)):
    meta = obj.get("transactionMetadata", {})
    print(label, "KEYS:",
          list(meta) if isinstance(meta, dict) else type(meta).__name__)
    if isinstance(meta, dict):
        print("INFERENCE:", str(meta.get("inference", "<ABSENT>"))[:500])
PY

echo "=== MAX EXECUTION MARKERS ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 1000 bplan-debug 2>&1 |
  grep -E 'BPLAN REAL MAX EXECUTION (START|PASS)|BPLAN RESPONSE ID MATCH' |
  tail -15
