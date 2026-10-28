cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/v1.168/model-settings.json")
data = json.loads(p.read_text())

print("ROOT TYPE:", type(data).__name__)
found = []

def walk(obj, path="$"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            location = f"{path}.{key}"
            if key.lower() in ("modelid", "expthrottlelabel"):
                found.append((location, value))
            if isinstance(value, (dict, list)):
                walk(value, location)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            walk(value, f"{path}[{i}]")

walk(data)

for location, value in found[:20]:
    print(f"{location} = {value!r}")

print("MATCHES:", len(found))
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
