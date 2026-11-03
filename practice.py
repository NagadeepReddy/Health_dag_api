python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
files = {
    "REQUEST": root / "artifacts/v1.113/core-artifact/test_samples/test_sample_1.json",
    "PYTORCH": root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json",
    "NATIVE MAX": Path("/tmp/bplan_response_trace.json"),
}

terms = (
    "category", "sourceSystem", "networkType",
    "deviceCategory", "customerInterests",
    "orderIntent", "passOnePlan", "isNewCustomer"
)

def inspect(obj, path="$", depth=0):
    if depth > 12:
        return
    if isinstance(obj, dict):
        for key, value in obj.items():
            if any(term.lower() in key.lower() for term in terms):
                if not isinstance(value, (dict, list)):
                    print(f"{path}.{key} = {str(value)[:150]}")
            inspect(value, f"{path}.{key}", depth+1)
    elif isinstance(obj, list):
        for i, value in enumerate(obj[:3]):
            inspect(value, f"{path}[{i}]", depth+1)

for name, file in files.items():
    print(f"\n=== {name} ===")
    if not file.is_file():
        print("MISSING:", file)
        continue
    data = json.loads(file.read_text())
    print("FILE:", file)
    print("TOP KEYS:", list(data) if isinstance(data, dict) else type(data).__name__)
    prediction = data.get("jsonData", {}).get("prediction", {}) if isinstance(data, dict) else {}
    print("PREDICTION KEYS:", list(prediction) if isinstance(prediction, dict) else "N/A")
    inspect(data)

print("\nBPLAN ROUTING INPUT COMPARISON COMPLETE")
PY
