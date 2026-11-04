cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json

root = Path("artifacts/v1.472")
p = root / "core-artifact/pipeline.py"
lines = p.read_text().splitlines()

print("=== EXACT DS FAILURE CONTEXT ===")
for n in range(3985, 4031):
    print(f"{n}: {lines[n-1]}")

print("\n=== WEB INTERACTION REFERENCES ===")
for n in range(3646, 4689):
    if "webInteraction_name" in lines[n-1]:
        print(f"{n}: {lines[n-1].strip()[:180]}")

print("\n=== SAMPLE INPUT NULL AUDIT ===")
body = json.loads(
    (root / "samples/sanity_input.json").read_text()
)

count = 0

def walk(obj, path="$"):
    global count
    if isinstance(obj, dict):
        if "webInteraction_name" in obj:
            count += 1
            v = obj["webInteraction_name"]
            page = obj.get("page")
            print(
                path,
                "TYPE:", type(v).__name__,
                "PAGE TYPE:", type(page).__name__,
                "PAGE NAME:",
                page.get("name") if isinstance(page, dict) else None
            )
        for k, v in obj.items():
            walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]")

walk(body)

print("WEB INTERACTION FIELDS:", count)
print("DIAGNOSIS: COMPLETE")
print("FILES MODIFIED: NONE")
print("ORIGINAL DS: UNCHANGED")
PY
