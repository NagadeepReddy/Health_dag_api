python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
files = {
    "PYTORCH": root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json",
    "MAX": Path("/tmp/bplan_native_response.json")
}

for name, path in files.items():
    obj = json.loads(path.read_text())
    print(f"\n=== {name} RESPONSE ===")

    for level, key in [
        ("TOP", None),
        ("jsonData", "jsonData"),
    ]:
        value = obj if key is None else obj.get(key)
        print(f"{level}: type={type(value).__name__}")
        if isinstance(value, dict):
            print("KEYS:", list(value.keys()))
            print("CONTENT:", json.dumps(value, default=str)[:1200])
        else:
            print("CONTENT:", str(value)[:1200])

a = json.loads(files["PYTORCH"].read_text()).get("jsonData")
b = json.loads(files["MAX"].read_text()).get("jsonData")

print("\n=== JSONDATA PARITY ===")
print("EXACT MATCH:", a == b)
PY
