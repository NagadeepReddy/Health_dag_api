python3 - <<'PY'
import ast, json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact")
tree = ast.parse((root / "pipeline.py").read_text())

print("=== CURRENT DS FALLBACK DEFINITIONS ===")
names = {
    "DEFAULT_PROPOSITION_LIST_BPLAN",
    "DEFAULT_PROPOSITION_LIST_TAB",
    "DEFAULT_PROPOSITION_LIST_CD",
}

for node in tree.body:
    if isinstance(node, ast.Assign):
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        for name in targets:
            if name not in names:
                continue
            try:
                value = ast.literal_eval(node.value)
                print("\n", name)
                for group, items in value.items():
                    if isinstance(items, list):
                        print(group, "COUNT:", len(items))
                        print("NAMES:", [
                            x.get("propositionName")
                            for x in items
                            if isinstance(x, dict)
                        ][:25])
            except Exception as e:
                print(name, "NOT STATIC:", type(e).__name__)

print("\n=== EXPECTED VS MAX ===")
files = {
    "EXPECTED": root / "test_samples/test_sample_myplan_bundle_output.json",
    "MAX": Path("/tmp/bplan_myplan_trace.json"),
}

for label, path in files.items():
    obj = json.loads(path.read_text())
    data = obj["jsonData"]
    if isinstance(data, str):
        data = json.loads(data)

    print("\n", label)
    for i, group in enumerate(data["prediction"]["ctaList"]):
        print("LIST", i, "COUNT", len(group))
        print("NAMES:", [
            x.get("propositionName")
            for x in group
            if isinstance(x, dict)
        ][:25])
PY
