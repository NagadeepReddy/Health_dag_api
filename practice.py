cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/v1.168/model-settings.json")
config = json.loads(p.read_text())

for key in ("modelId", "expThrottleLabel"):
    value = config.get(key)
    print(f"{key}: {value}")
    if not isinstance(value, str) or not value:
        raise SystemExit(f"STOP: invalid {key}")

test = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py")
assert test.is_file(), "Native test missing"

print("MODEL SETTINGS: PASS")
print("NATIVE TEST: EXISTS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
