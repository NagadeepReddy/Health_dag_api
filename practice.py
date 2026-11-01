ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import json, os
from pathlib import Path

root = Path(os.environ["ROOT"])
report = json.loads((root / "bplan_helper_weight_mapping.json").read_text())
manifest = json.loads((root / "max_weights/manifest.json").read_text())

aliases = {
    "item_embedding_weight": "item_embedding.weight",
    "item_meta_embedding_weight": "item_meta_embedding.weight",
    "item_pre_embedding_weight": "item_pre_embedding.weight",
    "page_embedding_weight": "page_embedding.weight",
    "page_meta_wide_dense_weight": "sequence_transformer.page_meta_wide_dense.weight",
    "page_meta_wide_dense_bias": "sequence_transformer.page_meta_wide_dense.bias",
    "seq_dense_weight": "seq_dense.weight",
    "seq_dense_bias": "seq_dense.bias",
}

fn_names = {
    "fn_attn_out_weight": "attn_out.weight",
    "fn_ff_out_1_weight": "ff_out.1.weight",
    "fn_fused_attn_ff_proj_weight": "fused_attn_ff_proj.weight",
    "fn_norm1_g": "norm1.g",
    "fn_norm2_g": "norm2.g",
}

resolved = {}
pending = {}

for filename, old_candidates in report.items():
    if old_candidates:
        continue

    stem = Path(filename).stem
    key = aliases.get(stem)

    if stem.startswith("fn_") and stem != "fn_rotary_emb_inv_freq":
        layer = 1 if stem.endswith("_layer1") else 0
        base = stem.removesuffix("_layer1")
        if base in fn_names:
            key = f"sequence_transformer.ptransformer.{layer}.fn.{fn_names[base]}"

    if key in manifest:
        resolved[filename] = key
    else:
        term = stem.replace("_", ".")
        hints = [
            k for k in manifest
            if k.endswith(term) or
            ("rotary_emb.inv_freq" in k and "rotary" in stem) or
            ("norm" in stem and "norm" in k and ".g" in k)
        ]
        pending[filename] = hints[:8]

out = root / "bplan_21_weight_resolution.json"
out.write_text(json.dumps({
    "resolved": resolved,
    "pending": pending
}, indent=2))

print("BPLAN WEIGHT NAME RESOLUTION: SAVED")
print("RESOLVED:", len(resolved))
print("NEEDS CONFIRMATION:", len(pending))
for name, hints in pending.items():
    print("CHECK:", name)
    print("CANDIDATES:", hints)
print("REPORT:", out)
PY
