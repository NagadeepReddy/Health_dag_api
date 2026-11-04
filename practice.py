cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import json
from pathlib import Path

root = Path("artifacts/v1.472/samples")

print("=== PZAAS REAL INPUT PREFLIGHT ===")

def walk(obj, path="$"):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")

valid = []

for file in sorted(root.glob("*.json")):
    if "output" in file.name.lower():
        continue

    try:
        data = json.loads(file.read_text())
    except (ValueError, OSError) as e:
        print(file.name, "INVALID JSON:", type(e).__name__)
        continue

    affected = []

    for path, obj in walk(data):
        page = obj.get("page")
        if not isinstance(page, dict):
            continue

        name = page.get("name", "")
        if not isinstance(name, str):
            continue

        if name.lower() not in ("gridwall_smartphones", "deals"):
            continue

        value = obj.get("webinteraction_name")

        if not isinstance(value, str):
            affected.append((path, name, type(value).__name__))

    print(file.name, "INVALID WEB INTERACTIONS:", len(affected))

    for path, name, kind in affected[:5]:
        print(" ", path, "| page:", name, "| value type:", kind)

    if not affected:
        valid.append(file.name)

print("\nPREFLIGHT-COMPATIBLE SAMPLES:", valid)
print("ORIGINAL DS: UNCHANGED")
print("MAX GRAPH: UNCHANGED")
PY
