cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/v1.168/samples/sanity_input.json")
data = json.loads(p.read_text())
matches = []

def walk(obj, path="$"):
    if isinstance(obj, dict):
        page = obj.get("page")
        if isinstance(page, dict) and page.get("name") in ("gridwall_smartphones", "deals"):
            value = obj.get("webinteraction_name")
            matches.append((path, page.get("name"), type(value).__name__, value is None))
        for k, v in obj.items():
            walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]")

walk(data)
print("MATCHING PAGE EVENTS:", len(matches))
for item in matches[:10]:
    print("PATH / PAGE / FIELD TYPE / IS NONE:", item)
print("DS CODE: UNCHANGED")
PY
