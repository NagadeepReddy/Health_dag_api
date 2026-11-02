python3 - <<'PY'
import json
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.110/core-artifact/test_samples/test_sample_1.json")
data = json.loads(p.read_text())
print("SAMPLE:", p)
print("ROOT TYPE:", type(data).__name__)
print("ROOT KEYS:", list(data) if isinstance(data, dict) else "not a dictionary")
print("JSON DATA KEYS:", list(data["jsonData"]) if isinstance(data, dict) and isinstance(data.get("jsonData"), dict) else "not present")
PY
