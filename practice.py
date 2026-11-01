ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import json, os
from pathlib import Path

root = Path(os.environ["ROOT"])
p = root / "bplan_all_90_weight_mapping.json"
data = json.loads(p.read_text())
manifest = json.loads((root / "max_weights/manifest.json").read_text())

fixes = {
    "seq_dense_bias.npy": "seq_dense.bias",
    "seq_dense_weight.npy": "seq_dense.weight",
}

print("CURRENT RESOLVED:", len(data["resolved"]))
print("ACTUAL AMBIGUOUS:", list(data["ambiguous"]))

updated = dict(data["resolved"])
remaining = dict(data["ambiguous"])

for basename, weight in fixes.items():
    matches = [
        name for name in remaining
        if Path(name).name == basename
    ]
    assert len(matches) == 1, f"STOP: expected one match for {basename}: {matches}"

    filename = matches[0]
    assert weight in remaining[filename], f"STOP: candidate missing: {weight}"
    assert weight in manifest, f"STOP: BPLAN tensor missing: {weight}"

    updated[filename] = weight
    del remaining[filename]
    print("MAPPED:", filename, "->", weight)

assert len(updated) == 90, f"STOP: resolved {len(updated)}/90"
assert not remaining and not data["missing"], "STOP: unresolved mappings remain"

data["resolved"] = updated
data["ambiguous"] = remaining
p.write_text(json.dumps(data, indent=2))

print("BPLAN 90 WEIGHT NAME MAPPINGS: PASS")
print("RESOLVED: 90 | AMBIGUOUS: 0 | MISSING: 0")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
