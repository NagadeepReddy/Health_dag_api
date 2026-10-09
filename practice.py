python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
'''        # Match original ParallelTransformerBlock head layout.
        # q: [batch, seq, 512] -> [batch, 2, seq, 256]
        # k/v: [batch, seq, 256] -> [batch, 1, seq, 256]''',
'''        # Verified directly against the real CTA PyTorch block:
        # fused_dims = (512, 256, 256, 2048)
        # Q  -> 2 x 256 heads
        # K/V -> 1 x 256 head (broadcast across Q heads during attention)'''
)

# Add verified block constants.
needle='''        super().__init__()
'''

replacement='''        super().__init__()

        # Verified from the real CTA ParallelTransformerBlock.
        self.heads = 2
        self.dim_head = 256
        self.scale = 256 ** -0.5
        self.fused_dims = (512, 256, 256, 2048)
'''

if needle not in s:
    raise SystemExit("Constructor location not found")

s=s.replace(needle,replacement,1)

with open(p,"w") as f:
    f.write(s)

print("CTA TRANSFORMER DIMENSIONS LOCKED")
PY
