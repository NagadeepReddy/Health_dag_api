cp artifacts/v1.168-max/cta_max/parallel_transformer_block.py \
   artifacts/v1.168-max/cta_max/parallel_transformer_block.py.bak_ff_ok && \
python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block.py")
s = p.read_text()

old_init = """        self.norm1 = RMSNorm(
            256,
            dtype=dtype,
            eps=1e-6,
        )
        self.fused_dims = (512, 256, 256, 2048)
"""

new_init = """        self.norm1 = RMSNorm(
            256,
            dtype=dtype,
            eps=1e-6,
        )
        self.norm2 = RMSNorm(
            2048,
            dtype=dtype,
            eps=1e-6,
        )
        self.fused_dims = (512, 256, 256, 2048)
"""

old_ff = """        ff1 = ff[..., :1024]
        ff3 = ff[..., 1024:]
        swiglu = ops.silu(ff1) * ff3
        ff_out = self.ff_out(swiglu)

        return attn_out + ff_out
"""

new_ff = """        ff = self.norm2(ff)
        ff1 = ff[..., :1024]
        ff3 = ff[..., 1024:]
        swiglu = ops.silu(ff1) * ff3
        ff_out = self.ff_out(swiglu)

        return attn_out + ff_out
"""

assert old_init in s, "STOP: init pattern not found"
assert old_ff in s, "STOP: ff pattern not found"

s = s.replace(old_init, new_init, 1)
s = s.replace(old_ff, new_ff, 1)

p.write_text(s)
print("REAL MAX BLOCK PATCHED")
PY
