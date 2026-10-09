python - <<'PY'
p="artifacts/v1.168-max/cta_max/run_transformer_max.py"

with open(p) as f:
    s=f.read()

repls = {
"sequence_transformer.ptransformer.0.fn.norm1.g.npy":
"fn_norm1_g.npy",

"sequence_transformer.ptransformer.0.fn.norm2.g.npy":
"fn_norm2_g.npy",

"sequence_transformer.ptransformer.0.fn.fused_attn_ff_proj.weight.npy":
"fn_fused_attn_ff_proj_weight.npy",

"sequence_transformer.ptransformer.0.fn.attn_out.weight.npy":
"fn_attn_out_1_weight.npy",

"sequence_transformer.ptransformer.0.fn.ff_out.1.weight.npy":
"fn_ff_out_1_weight.npy",

"sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq.npy":
"fn_rotary_emb_inv_freq.npy",
}

for old,new in repls.items():
    s=s.replace(old,new)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER EXISTING WEIGHT FILENAMES MAPPED")
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_max.py
