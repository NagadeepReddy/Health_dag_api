python3 - <<'PY'
import json, re
from pathlib import Path

text = Path("/tmp/cta_pytorch_tiles_response.json").read_text()
decoder = json.JSONDecoder()

pt = None
for match in re.finditer(r'\{\s*"jsonData"\s*:', text):
    try:
        pt, _ = decoder.raw_decode(text[match.start():])
        break
    except json.JSONDecodeError:
        pass

if pt is None:
    raise SystemExit("PyTorch response not found")

mx = json.loads(Path("/tmp/cta_max_tiles_response.json").read_text())

p = pt["jsonData"]["prediction"]
m = mx["jsonData"]["prediction"]

print("FULL PREDICTION EXACT MATCH:", p == m)
print("MATCHING FIELDS:", sorted(k for k in p.keys() & m.keys() if p[k] == m[k]))
print("DIFFERENT FIELDS:", sorted(k for k in p.keys() & m.keys() if p[k] != m[k]))
print("MISSING IN MAX:", sorted(p.keys() - m.keys()))
print("EXTRA IN MAX:", sorted(m.keys() - p.keys()))
PY
