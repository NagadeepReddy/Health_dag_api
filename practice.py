python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

# Remove MAX RMSNorm module construction.
s=s.replace(
'''        self.norm1 = RMSNorm(256, dtype)
        self.norm2 = RMSNorm(2048, dtype)''',
'''        # RMSNorm is implemented explicitly in __call__ so norm1/norm2
        # can use separate CTA checkpoint weights without registry collision.'''
)

# Replace the two RMSNorm calls with explicit RMSNorm math.
s=s.replace(
'''x_norm = self.norm1(x)''',
'''norm1_g = self.norm1_g
        variance1 = ops.mean(x * x, axis=-1, keepdims=True)
        x_norm = x * ops.rsqrt(variance1 + 1e-6)
        x_norm = x_norm * norm1_g'''
)

s=s.replace(
'''return self.norm2(ff) + self.ff_out(ff)''',
'''variance2 = ops.mean(ff * ff, axis=-1, keepdims=True)
        ff_norm = ff * ops.rsqrt(variance2 + 1e-6)
        ff_norm = ff_norm * self.norm2_g
        return ff_norm + self.ff_out(ff)'''
)

# Add explicit weight placeholders beside the existing module initialization.
needle='''        self.scale = 256 ** -0.5'''
replacement='''        self.scale = 256 ** -0.5

        self.norm1_g = Weight(
            "sequence_transformer.ptransformer.0.norm1.weight",
            dtype=dtype,
            shape=[256],
            device=device,
        )
        self.norm2_g = Weight(
            "sequence_transformer.ptransformer.0.norm2.weight",
            dtype=dtype,
            shape=[2048],
            device=device,
        )'''

s=s.replace(needle, replacement)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER EXPLICIT RMSNORM ADDED")
PY
