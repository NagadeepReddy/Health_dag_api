cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
d = json.loads(p.read_text())

events = d.get("Events", {})
print("EVENTS TYPE:", type(events).__name__)

if isinstance(events, dict):
    for key, value in events.items():
        print("EVENT FIELD:", key, "| TYPE:", type(value).__name__,
              "| COUNT:", len(value) if isinstance(value, (list, dict)) else "N/A")
        if isinstance(value, list):
            print("ITEM TYPES:", [type(x).__name__ for x in value[:5]])

print("JSON STRUCTURE CHECK: COMPLETE")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
