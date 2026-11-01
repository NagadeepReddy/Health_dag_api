cd /application1/sajjna8/rt-pzai-bplan-v1 && python3 - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/v1.113/samples/sanity_input.json")
data = json.loads(p.read_text())

print("Sample exists:", p.exists())
print("Top-level keys:", list(data) if isinstance(data, dict) else type(data).__name__)
print("Has nested jsonData:", isinstance(data, dict) and "jsonData" in data)
print("Sample size:", p.stat().st_size, "bytes")
PY
