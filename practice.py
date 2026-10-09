python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
'''q, k, v, ff = self.fused_attn_ff_proj(x_norm).split(
            [512, 256, 256, 2048],
            axis=-1,
        )''',
'''q, k, v, ff = ops.split(
            self.fused_attn_ff_proj(x_norm),
            [512, 256, 256, 2048],
            axis=-1,
        )'''
)

with open(p,"w") as f:
    f.write(s)

print("MAX TENSOR SPLIT FIXED")
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_max.py
