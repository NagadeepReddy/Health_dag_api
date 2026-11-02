python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
files = [
    root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json",
    Path("/tmp/bplan_native_response.json")
]

def find_predictions(obj):
    if isinstance(obj, dict):
        for key in ("propositionList", "ctaList"):
            if key in obj:
                return obj[key]
        for value in obj.values():
            result = find_predictions(value)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for value in obj:
            result = find_predictions(value)
            if result is not None:
                return result
    return None

a, b = [find_predictions(json.loads(p.read_text())) for p in files]

print("=== BPLAN BUSINESS PARITY ===")
if a is None or b is None:
    print("Prediction structure not found.")
    for p in files:
        obj = json.loads(p.read_text())
        print(p.name, list(obj) if isinstance(obj, dict) else type(obj).__name__)
else:
    print("PYTORCH TYPE:", type(a).__name__)
    print("MAX TYPE:", type(b).__name__)
    print("EXACT MATCH:", a == b)
    if isinstance(a, list) and isinstance(b, list):
        print("COUNTS:", len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            print(f"ITEM {i}: {'PASS' if x == y else 'DIFFERENT'}")
            if x != y and i < 4:
                print("PYTORCH:", str(x)[:350])
                print("MAX:", str(y)[:350])
PY
