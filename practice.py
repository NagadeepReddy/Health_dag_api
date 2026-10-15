python3 - <<'PY'
import json
from pathlib import Path

for version in ("v1.167", "v1.168"):
    p = Path(f"artifacts/{version}/samples/sanity_input.json")
    data = json.loads(p.read_text())
    events = data.get("Events", {}).get("eventValues", [])

    matches = [
        (i, e) for i, e in enumerate(events)
        if isinstance(e, dict)
        and isinstance(e.get("page"), dict)
        and str(e["page"].get("name", "")).lower() == "gridwall_smartphones"
    ]
    valid = [
        i for i, e in matches
        if isinstance(e.get("webinteraction_name"), str)
        and len(e["webinteraction_name"].split("|")) > 7
    ]

    print(version, "MATCHING EVENTS:", len(matches),
          "VALID:", len(valid),
          "INVALID/MISSING:", len(matches) - len(valid))
    if matches:
        print("EVENT FIELDS:", sorted(matches[0][1].keys()))
PY
