python3 - <<'PY'
import json, re
from pathlib import Path

pt_path = Path("/tmp/cta_pytorch_tiles_response.json")
mx_path = Path("/tmp/cta_max_tiles_response.json")

text = pt_path.read_text()
decoder = json.JSONDecoder()
pt = None

for match in re.finditer(r'\{\s*"jsonData"\s*:', text):
    try:
        pt, _ = decoder.raw_decode(text[match.start():])
        break
    except json.JSONDecodeError:
        continue

if pt is None:
    raise SystemExit("PYTORCH JSON NOT FOUND — no files changed")

mx = json.loads(mx_path.read_text())

p = pt["jsonData"]["prediction"]
m = mx["jsonData"]["prediction"]

print("PYTORCH OFFERS:", len(p.get("offerList", [])))
print("MAX OFFERS:", len(m.get("offerList", [])))
print("OFFER LIST EXACT MATCH:", p.get("offerList") == m.get("offerList"))
print("RECOMMENDATION FLAG MATCH:", p.get("isNewRcmd") == m.get("isNewRcmd"))
PY
