python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

# Add Weight import.
s=s.replace(
    "from max.nn import Linear, RMSNorm",
    "from max.nn import Linear, RMSNorm, Weight"
)

# Add the real rotary checkpoint weight to the module.
needle = '''        self.norm2 = RMSNorm(2048, dtype, name="sequence_transformer.ptransformer.0.norm2")
'''

replacement = '''        self.norm2 = RMSNorm(2048, dtype, name="sequence_transformer.ptransformer.0.norm2")

        # Real CTA checkpoint weight: rotary_emb.inv_freq, shape (128,)
        self.rotary_inv_freq = Weight(
            "sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq",
            dtype=dtype,
            shape=[128],
            device=device,
        )
'''

if needle not in s:
    raise SystemExit("Expected norm2 section not found — file left unchanged.")

s=s.replace(needle, replacement)

with open(p,"w") as f:
    f.write(s)

print("ROTARY REAL WEIGHT WIRED")
PY
