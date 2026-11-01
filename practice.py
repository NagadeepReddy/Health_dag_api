ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import json, os
from pathlib import Path

root = Path(os.environ["ROOT"])
p = root / "bplan_all_90_weight_mapping.json"
data = json.loads(p.read_text())
manifest = json.loads((root / "max_weights/manifest.json").read_text())

fixes = {
    "grecbase_integration_weights/seq_dense_bias.npy": "seq_dense.bias",
    "grecbase_integration_weights/seq_dense_weight.npy": "seq_dense.weight",
}

assert len(data["resolved"]) == 88
assert set(data["ambiguous"]) == set(fixes)
assert not data["missing"]

for filename, key in fixes.items():
    assert key in data["ambiguous"][filename]
    assert key in manifest
    data["resolved"][filename] = key
    del data["ambiguous"][filename]
    print("MAPPED:", filename, "->", key)

assert len(data["resolved"]) == 90
assert not data["ambiguous"] and not data["missing"]

p.write_text(json.dumps(data, indent=2))

print("BPLAN 90 WEIGHT NAME MAPPINGS: PASS")
print("RESOLVED: 90")
print("AMBIGUOUS: 0")
print("MISSING: 0")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
