python3 - <<'PY'
import json
from pathlib import Path

src = Path("artifacts/v1.168/samples/sanity_input.json")
dst = Path("/tmp/cta_max_smoketest.json")

data = json.loads(src.read_text())
count = 0

for event in data["Events"]["eventValues"]:
    if (isinstance(event, dict)
        and isinstance(event.get("page"), dict)
        and str(event["page"].get("name", "")).lower() == "gridwall_smartphones"
        and event.get("webinteraction_name") is None):
        event["webinteraction_name"] = ""
        count += 1

dst.write_text(json.dumps(data))
dst.chmod(0o600)
print("TEMPORARY TEST JSON READY")
print("Missing fields normalized:", count)
print("Original JSON unchanged")
PY
