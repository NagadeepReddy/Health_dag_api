python3 - <<'PY'
import json
from pathlib import Path

base = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples")
files = {
    "MAX MYPLAN": Path("/tmp/bplan_myplan_trace.json"),
    "EXPECTED MYPLAN": base / "test_sample_myplan_bundle_output.json",
    "MAX FIRST TEST": Path("/tmp/bplan_verified_result.json"),
}

def inspect(label, path):
    print(f"\n=== {label} ===")
    if not path.is_file():
        print("MISSING:", path)
        return

    obj = json.loads(path.read_text())
    data = obj.get("jsonData", {})
    if isinstance(data, str):
        data = json.loads(data)

    meta = obj.get("transactionMetadata", {})
    if not isinstance(meta, dict):
        meta = {}

    print("Metadata keys:", list(meta))
    for key in ("pre_out", "inference", "inference_raw"):
        value = meta.get(key, "<ABSENT>")
        print(key, ":", str(value)[:1200])

    prediction = data.get("prediction", {}) if isinstance(data, dict) else {}
    lists = prediction.get("ctaList", [])
    print("CTA LIST SIZES:", [len(x) if isinstance(x, list) else "N/A" for x in lists])

    for index, group in enumerate(lists):
        if not isinstance(group, list):
            continue
        ids = [
            item.get("propositionId")
            for item in group[:8]
            if isinstance(item, dict)
        ]
        print(f"CTA LIST {index} FIRST IDS:", ids)

for label, path in files.items():
    inspect(label, path)

print("\n=== ORIGINAL PIPELINE FALLBACK CONDITION ===")
p = base.parent / "pipeline.py"
lines = p.read_text(errors="replace").splitlines()
for n in range(3996, 4015):
    print(f"{n}: {lines[n-1].strip()}")
PY
