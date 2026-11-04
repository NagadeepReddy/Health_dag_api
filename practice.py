cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json

root = Path("artifacts/v1.472-max/pzaas_max")
p = root / "sequence_transformer_max.py"

manifest = json.loads(
    (root / "pzaas_base_weights/manifest.json").read_text()
)
cfg = json.loads(
    Path("artifacts/v1.472/config/torch_model_params_base.json").read_text()
)
if isinstance(cfg, list):
    cfg = cfg[0]

size = manifest["sequence_transformer.item_meta_embedding.weight"]["shape"][0]
assert size == cfg["item_meta_dim"] == 522

source = p.read_text()

if source.count("vocab_size=523") == 1:
    updated = source.replace("vocab_size=523", "vocab_size=522", 1)
    compile(updated, str(p), "exec")
    p.write_text(updated)
    print("PZAAS ITEM META DIMENSION: UPDATED")
elif source.count("vocab_size=522") == 1:
    print("PZAAS ITEM META DIMENSION: ALREADY CORRECT")
else:
    raise SystemExit("STOP: Unexpected vocabulary definition")

for f in root.glob("*.py"):
    compile(f.read_text(), str(f), "exec")

print("ITEM META DIMENSION:", size)
print("GRAPH PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("MAX GRAPH COMPILATION: PENDING")
PY
