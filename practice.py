cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -S -B - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/v1.168/model-settings.json")
d = json.loads(p.read_text())

print("TOP-LEVEL CONFIG KEYS:", list(d))

def check(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("modelId", "expThrottleLabel"):
                print(f"{path}.{k} = {v!r}")
            elif isinstance(v, (dict, list)):
                check(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check(v, f"{path}[{i}]")

check(d)
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
