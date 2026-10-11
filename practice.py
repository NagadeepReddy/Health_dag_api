python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")

files = {
    "parallel_transformer_block_intermediate.py": "parallel_transformer_block_layer1_ff.py",
    "parallel_transformer_graph_intermediate.py": "parallel_transformer_graph_layer1_ff.py",
    "run_transformer_intermediate_parity.py": "run_transformer_layer1_ff.py",
}

prepared = {}

for src_name, dst_name in files.items():
    src, dst = base / src_name, base / dst_name
    assert src.is_file(), f"STOP: missing {src_name}"
    assert not dst.exists(), f"STOP: already exists {dst_name}"

    s = src.read_text()

    if src_name.startswith("parallel_transformer_block_"):
        assert "fn_norm2_g.npy" in s
        s = s.replace("fn_norm2_g.npy", "fn_norm2_g_layer1.npy")
    elif src_name.startswith("parallel_transformer_graph_"):
        assert "from parallel_transformer_block_intermediate import" in s
        s = s.replace(
            "from parallel_transformer_block_intermediate import",
            "from parallel_transformer_block_layer1_ff import"
        )
    else:
        assert "from parallel_transformer_graph_intermediate import" in s
        assert "transformer_pytorch_output.npy" in s
        s = s.replace(
            "from parallel_transformer_graph_intermediate import",
            "from parallel_transformer_graph_layer1_ff import"
        )
        s = s.replace(
            "transformer_pytorch_output.npy",
            "transformer_pytorch_layer1_ff.npy"
        )
        for name in [
            "fn_norm1_g",
            "fn_norm2_g",
            "fn_fused_attn_ff_proj_weight",
            "fn_attn_out_weight",
            "fn_ff_out_1_weight",
        ]:
            s = s.replace(name + ".npy", name + "_layer1.npy")

    s = s.replace(
        "sequence_transformer.ptransformer.0.",
        "sequence_transformer.ptransformer.1."
    )
    ast.parse(s)
    prepared[dst] = s

for dst, s in prepared.items():
    dst.write_text(s)
    print("CREATED:", dst.name)

print("BLOCK-1 FF DIAGNOSTICS READY")
print("ORIGINAL MAX AND DS FILES UNCHANGED")
PY
