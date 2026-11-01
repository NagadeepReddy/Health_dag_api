ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import json, os
from pathlib import Path

root = Path(os.environ["ROOT"])
mapping = json.loads((root / "bplan_helper_weight_mapping.json").read_text())
fixed = json.loads((root / "bplan_21_weight_resolution.json").read_text())["resolved"]
manifest = json.loads((root / "max_weights/manifest.json").read_text())

resolved, ambiguous, missing = {}, {}, {}

for filename, candidates in mapping.items():
    if filename in fixed:
        key = fixed[filename]
    elif len(candidates) == 1:
        key = candidates[0]
    else:
        ambiguous[filename] = candidates
        continue

    if key not in manifest:
        missing[filename] = key
    else:
        resolved[filename] = key

report = {
    "resolved": resolved,
    "ambiguous": ambiguous,
    "missing": missing
}
out = root / "bplan_all_90_weight_mapping.json"
out.write_text(json.dumps(report, indent=2))

print("TOTAL HELPER FILES:", len(mapping))
print("UNIQUELY MAPPED:", len(resolved))
print("AMBIGUOUS:", len(ambiguous))
print("MISSING:", len(missing))
for name, candidates in ambiguous.items():
    print("AMBIGUOUS:", name, candidates[:5])
for name, key in missing.items():
    print("MISSING:", name, key)
print("REPORT:", out)
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
