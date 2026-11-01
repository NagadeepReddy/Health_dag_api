ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import json, os
from pathlib import Path

p = Path(os.environ["ROOT"]) / "bplan_all_90_weight_mapping.json"
data = json.loads(p.read_text())

fixes = {
    "grecbase_integration_weights/seq_dense.bias.npy": "seq_dense.bias",
    "grecbase_integration_weights/seq_dense.weight.npy": "seq_dense.weight",
}

assert len(data["resolved"]) == 88
assert set(data["ambiguous"]) == set(fixes)
assert not data["missing"]

for filename, key in fixes.items():
    assert key in data["ambiguous"][filename], f"Invalid mapping: {filename}"

for filename, key in fixes.items():
    data["resolved"][filename] = key
    del data["ambiguous"][filename]
    print("MAPPED:", filename, "->", key)

assert len(data["resolved"]) == 90
assert not data["ambiguous"]

p.write_text(json.dumps(data, indent=2))

print("BPLAN 90 WEIGHT NAME MAPPINGS: PASS")
print("RESOLVED: 90 | AMBIGUOUS: 0 | MISSING: 0")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
