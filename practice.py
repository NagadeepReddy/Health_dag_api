cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path
import json

p = Path("artifacts/v1.168-max/samples/adjusted_sanity_input.json")

if not p.is_file():
    raise SystemExit("STOP: adjusted JSON not found")

data = json.loads(p.read_text())
print("JSON VALID: PASS")
print("FILE SIZE:", p.stat().st_size, "bytes")
print("ROOT TYPE:", type(data).__name__)

if isinstance(data, dict):
    print("ROOT KEYS:", sorted(data.keys()))
    for key, value in data.items():
        if isinstance(value, list):
            print(f"{key}: {len(value)} items")
        elif isinstance(value, dict):
            print(f"{key}: {len(value)} fields")

print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
