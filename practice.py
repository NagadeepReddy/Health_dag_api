cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json

r = Path("artifacts/v1.472")
g = Path("artifacts/v1.472-max/pzaas_max")
m = json.loads((g/"pzaas_base_weights/manifest.json").read_text())
cfg = json.loads((r/"config/torch_model_params_base.json").read_text())
if isinstance(cfg, list):
    cfg = cfg[0]

print("=== PZAAS CONFIG ===")
for k in ("seq_dim", "item_meta_dim", "item_embed_dim"):
    print(k, cfg.get(k))

print("\n=== TRAINED EMBEDDING SHAPES ===")
for k in ("sequence_transformer.item_embedding.weight",
          "sequence_transformer.item_meta_embedding.weight",
          "sequence_transformer.seq_dense.weight"):
    print(k, m[k]["shape"])

print("\n=== ORIGINAL DS EMBEDDING LOGIC ===")
p = r/"utils/dependency-utils/models.py"
s = p.read_text().splitlines()
for i, line in enumerate(s, 1):
    if "item_meta_embedding" in line or "item_meta_dim" in line:
        print(f"{i}: {line.strip()[:180]}")

print("\n=== MAX GRAPH EMBEDDING LOGIC ===")
p = g/"sequence_transformer_max.py"
s = p.read_text().splitlines()
for i, line in enumerate(s, 1):
    if "vocab_size" in line or "item_meta_embedding" in line:
        print(f"{i}: {line.strip()[:180]}")

print("\nDIMENSION VERIFICATION: INSPECTED")
print("NO FILES MODIFIED")
PY
