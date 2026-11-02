python3 - <<'PY'
from pathlib import Path
import json

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact")
lines = (root / "pipeline.py").read_text(errors="replace").splitlines()

print("=== ORIGINAL DS BUSINESS RULE CALLS ===")
terms = (
    "self.add_disney_family(",
    "self.add_travelpass(",
    "self.postprocess(",
    "self.inference("
)

for i, line in enumerate(lines):
    if any(t in line for t in terms):
        print(f"\n--- LINE {i+1} ---")
        for j in range(max(0, i-5), min(len(lines), i+7)):
            print(f"{j+1}: {lines[j][:160]}")

print("\n=== MYPLAN EXPECTED VS ACTUAL IDS ===")
files = {
    "EXPECTED": root / "test_samples/test_sample_myplan_bundle_output.json",
    "MAX HTTP": Path("/tmp/bplan_myplan_trace.json")
}

results = {}
for label, path in files.items():
    if not path.is_file():
        raise SystemExit(f"Missing: {path}")
    obj = json.loads(path.read_text())
    data = obj["jsonData"]
    if isinstance(data, str):
        data = json.loads(data)
    groups = data["prediction"]["ctaList"]
    results[label] = [
        [str(x.get("propositionId")) for x in group]
        for group in groups
    ]

for i, (expected, actual) in enumerate(zip(
    results["EXPECTED"], results["MAX HTTP"]
)):
    print(f"\nLIST {i}")
    print("Expected count:", len(expected))
    print("Actual count:", len(actual))
    print("Added IDs:", [x for x in actual if x not in expected])
    print("Missing IDs:", [x for x in expected if x not in actual])
PY
