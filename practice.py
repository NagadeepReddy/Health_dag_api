cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
import json
from pathlib import Path

files = {
    "WORKING REQUEST": Path("artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"),
    "SECOND REQUEST": Path("artifacts/v1.168-max/test-results/cta_max_tiles_smoketest_input.json"),
    "THIRD REQUEST": Path("artifacts/v1.168/samples/sanity_input.json"),
}

def inspect(obj, path="$"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            current = f"{path}.{key}"
            if "webinteraction" in key.lower():
                print(
                    "FIELD:", current,
                    "| TYPE:", type(value).__name__,
                    "| HAS VALUE:", value not in (None, "")
                )
            inspect(value, current)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            inspect(value, f"{path}[{i}]")

for name, path in files.items():
    print("\n===", name, "===")
    data = json.loads(path.read_text())
    inspect(data)
    print("ROOT KEYS:", sorted(data.keys()))

print("\nFILES MODIFIED: NONE")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
