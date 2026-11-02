
python3 - <<'PY'
import json
from pathlib import Path

base = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples")

files = {
    "MYPLAN MAX": Path("/tmp/bplan_myplan_trace.json"),
    "MYPLAN EXPECTED": base / "test_sample_myplan_bundle_output.json",
    "FIRST MAX TEST": Path("/tmp/bplan_verified_result.json"),
}

for label, path in files.items():
    print(f"\n=== {label} ===")

    if not path.is_file():
        print("FILE MISSING")
        continue

    obj = json.loads(path.read_text())
    meta = obj.get("transactionMetadata", {})
    data = obj.get("jsonData", {})

    if isinstance(data, str):
        data = json.loads(data)

    if not isinstance(meta, dict):
        meta = {}

    pre = meta.get("pre_out", {})
    if not isinstance(pre, dict):
        pre = {}

    deep = pre.get("deep_cols", {})
    if not isinstance(deep, dict):
        deep = {}

    print("Inference recorded:", "inference" in meta)
    print("Deep profile available:",
          deep.get("bplan_cd", "n/a"),
          deep.get("data_tier_fin", "n/a"))

    prediction = data.get("prediction", {})
    lists = prediction.get("ctaList", [])

    print("CTA list sizes:",
          [len(x) if isinstance(x, list) else "N/A"
           for x in lists])

    for i, group in enumerate(lists):
        if isinstance(group, list):
            print(f"List {i} IDs:",
                  [x.get("propositionId")
                   for x in group
                   if isinstance(x, dict)][:20])

print("\n=== FALLBACK RULE ===")
print("Missing bplan_cd AND data_tier_fin triggers")
print("the original pipeline's default recommendation path.")
PY
