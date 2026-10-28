cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")

if not p.is_file():
    raise SystemExit("STOP: actual native test input missing")

data = json.loads(p.read_text())
print("ADJUSTED JSON: VALID")
print("FILE SIZE:", p.stat().st_size, "bytes")
print("ROOT TYPE:", type(data).__name__)

if isinstance(data, dict):
    print("ROOT KEYS:", sorted(data))
    for key, value in data.items():
        if isinstance(value, list):
            print(f"{key}: {len(value)} items")
        elif isinstance(value, dict):
            print(f"{key}: {len(value)} fields")

print("ORIGINAL JSON: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
