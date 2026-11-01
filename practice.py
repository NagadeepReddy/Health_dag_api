ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os, json
from pathlib import Path

root = Path(os.environ["ROOT"])
p = root / "bplan_21_weight_resolution.json"
data = json.loads(p.read_text())
manifest = json.loads((root / "max_weights/manifest.json").read_text())

fixes = {
    "fn_rotary_emb_inv_freq.npy": "att_pooling.rotary_emb.inv_freq",
    "out_norm1_g.npy": "sequence_transformer.out_norm1.g",
    "out_norm2_g.npy": "sequence_transformer.out_norm2.g",
}

resolved = data["resolved"]
pending = data["pending"]

assert len(resolved) == 18 and len(pending) == 3
assert {Path(k).name for k in pending} == set(fixes)

for filename in list(pending):
    weight = fixes[Path(filename).name]
    assert weight in manifest, f"Missing BPLAN tensor: {weight}"
    resolved[filename] = weight
    del pending[filename]
    print("MAPPED:", filename, "->", weight)

assert len(resolved) == 21 and not pending
assert all(weight in manifest for weight in resolved.values())

p.write_text(json.dumps(data, indent=2))

print("BPLAN 21 WEIGHT NAME MAPPINGS: PASS")
print("RESOLVED:", len(resolved))
print("PENDING:", len(pending))
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
