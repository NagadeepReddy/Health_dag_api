python3 - <<'PY'
import json
from pathlib import Path

src = Path("/tmp/cta_max_smoketest.json")
dst = Path("/tmp/cta_max_tiles_test.json")

data = json.loads(src.read_text())
print("Original category:", data["ClientFeature"]["contextInfo"]["category"])

data["ClientFeature"]["contextInfo"]["category"] = "Tiles"

dst.write_text(json.dumps(data))
dst.chmod(0o600)

print("Test category:", data["ClientFeature"]["contextInfo"]["category"])
print("INFERENCE ROUTE TEST JSON: READY")
print("Original files unchanged")
PY
