python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
'''        self.ff_out = Linear(
            1024, 256, dtype, device,
            has_bias=False,
            name="sequence_transformer.ptransformer.0.ff_out.1",
        )
''',
'''        self.ff_out = Linear(
            1024, 256, dtype, device,
            has_bias=False,
            name="sequence_transformer.ptransformer.0.ff_out.1",
        )

    def __call__(self, x: TensorValue):
        # Original CTA flow:
        # norm1 -> fused projection -> Q/K/V/FF split
        x_norm = self.norm1(x)
        q, k, v, ff = self.fused_attn_ff_proj(x_norm).split(
            [512, 256, 256, 2048],
            axis=-1,
        )
        return q, k, v, ff
'''
)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER QKV FF FRONTEND ADDED")
PY
