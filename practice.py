cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
import json
import os
from pathlib import Path

src = Path("artifacts/v1.168/samples/sanity_input.json")
dst = Path("artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")

if not src.is_file() or dst.exists():
    raise SystemExit("STOP: source missing or adjusted file already exists")

space = os.statvfs(dst.parent)
if space.f_bavail * space.f_frsize < 50 * 1024 * 1024:
    raise SystemExit("STOP: insufficient space on /application1")

data = json.loads(src.read_text())
counts = {"webinteraction_name": 0, "category": 0}

def adjust(obj):
    if isinstance(obj, dict):
        if "webinteraction_name" in obj and obj["webinteraction_name"] is None:
            obj["webinteraction_name"] = ""
            counts["webinteraction_name"] += 1
        if obj.get("category") == "Smartphones":
            obj["category"] = "Tiles"
            counts["category"] += 1
        for value in obj.values():
            adjust(value)
    elif isinstance(obj, list):
        for value in obj:
            adjust(value)

adjust(data)

if counts["webinteraction_name"] != 6:
    raise SystemExit(f"STOP: expected 6 null fields, found {counts['webinteraction_name']}")

with dst.open("x") as f:
    json.dump(data, f)

print("ADJUSTED TEST JSON: CREATED")
print("NULL FIELDS FIXED:", counts["webinteraction_name"])
print("CATEGORY ADJUSTMENTS:", counts["category"])
print("FILE:", dst)
print("ORIGINAL JSON: UNCHANGED")
print("DS CODE: UNCHANGED")
PY
