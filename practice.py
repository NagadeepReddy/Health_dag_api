cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json, ast

root = Path("artifacts/v1.472-max/pzaas_max")
manifest = json.loads(
    (root/"pzaas_base_weights/manifest.json").read_text()
)

print("=== PZAAS GRAPH WEIGHT COMPATIBILITY ===")

for name in [
    "seq_dense.weight",
    "seq_dense.bias",
    "att_pooling.norm1.g",
    "att_pooling.norm2.g",
    "att_pooling.rotary_emb.inv_freq",
    "sequence_transformer.seq_dense.weight",
    "sequence_transformer.ptransformer.0.fn.fused_attn_ff_proj.weight",
    "sibling_context_head.deep_dense.weight",
    "context_head.deep_dense.weight",
    "remove_tasks_dense1.weight"
]:
    item = manifest.get(name)
    print(
        ("PASS" if item else "MISSING"),
        name,
        item["shape"] if item else ""
    )

print("\n=== LEGACY DEPENDENCIES ===")
for p in sorted(root.glob("*.py")):
    if p.name == "pzaas_weight_loader.py":
        continue
    lines = p.read_text().splitlines()
    refs = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if "v1.168" in line or "torch" in line.lower()
    ]
    if refs:
        print(p.name)
        for i, line in refs[:5]:
            print(f"  {i}: {line[:130]}")

print("\nPZAAS WEIGHT COMPATIBILITY CHECK: COMPLETE")
print("NO FILES MODIFIED")
PY
