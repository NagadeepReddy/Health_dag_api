cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.472-max/pzaas_max")
files = {
    "PYTORCH": Path("artifacts/v1.472/utils/dependency-utils/models.py"),
    "MAX BLOCK": base / "parallel_transformer_block_2layers.py",
    "MAX FUSION": base / "grecbase_fusion_full_head_72_max.py",
}

patterns = {
    "PYTORCH": [
        "x_out += x", "self.heads", "q_shape",
        "apply_rotary_pos_emb", "create_key_padding_mask",
        "masked_fill", "self.scale", "self.norm2(ff)"
    ],
    "MAX BLOCK": [
        "q.reshape", "k.reshape", "v.reshape",
        "apply_rotary_pos_emb_max", "self.scale",
        "valid_length", "ops.where", "return attn_out"
    ],
    "MAX FUSION": [
        "valid_length =", "sx1 =", "sx2 =",
        "seq_raw =", "graph.output"
    ]
}

print("=== PZAAS FIRST-DIVERGENCE CHECK ===")
for name, path in files.items():
    print(f"\n{name}:")
    if not path.is_file():
        print("BLOCKED: file not found:", path)
        continue
    lines = path.read_text().splitlines()
    for term in patterns[name]:
        hits = [(i, line.strip()) for i, line in enumerate(lines, 1)
                if term in line]
        if hits:
            for i, line in hits[:2]:
                print(f"{i}: {line}")
        else:
            print("NOT FOUND:", term)

print("\nORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: RESOLVE FIRST SEQUENCE DIVERGENCE")
PY
