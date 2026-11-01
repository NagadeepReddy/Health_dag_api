cd /application1/sajjna8/rt-pzai-bplan-v1 && python3 - <<'PY'
import json
from pathlib import Path

src = Path("artifacts/v1.113/samples/sanity_input.json")
dst = Path("artifacts/v1.113-max/maxserve_bplan_extension/bplan_sanity_features.json")

data = json.loads(src.read_text())
features = data["serviceRequest"]["rtModel"]["rtModelReq"][0]["features"]

assert isinstance(features, dict)
assert "profile" in features

dst.write_text(json.dumps(features, indent=2))

print("BPLAN INPUT EXTRACTION: PASS")
print("Feature keys:", list(features))
print("Test fixture:", dst)
print("Original sample: unchanged")
PY
