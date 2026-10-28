cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
import json
import os
from pathlib import Path

src = Path("artifacts/v1.168/samples/sanity_input.json")
dst = Path("artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")

if not src.is_file() or dst.exists():
    raise SystemExit("STOP: source missing or destination already exists")

fs = os.statvfs(dst.parent)
if fs.f_bavail * fs.f_frsize < 50 * 1024 * 1024:
    raise SystemExit("STOP: insufficient disk space")

data = json.loads(src.read_text())
fixed = 0

def adjust(obj):
    global fixed
    if isinstance(obj, dict):
        page = obj.get("page")
        if (
            isinstance(page, dict)
            and page.get("name") in ("gridwall_smartphones", "deals")
            and obj.get("webinteraction_name") is None
        ):
            obj["webinteraction_name"] = ""
            fixed += 1
        for value in obj.values():
            adjust(value)
    elif isinstance(obj, list):
        for value in obj:
            adjust(value)

adjust(data)

if fixed != 6:
    raise SystemExit(f"STOP: expected 6 events, found {fixed}")

with dst.open("x") as f:
    json.dump(data, f)

print("ADJUSTED TEST JSON: CREATED")
print("MISSING FIELDS FIXED:", fixed)
print("ORIGINAL JSON: UNCHANGED")
print("DS CODE: UNCHANGED")
PY
