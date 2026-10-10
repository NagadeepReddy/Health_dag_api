python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block.py")
s = p.read_text()

old_init = "self.norm1 = RMSNorm("
assert s.count(old_init) == 1, "norm1 initialization not found uniquely"

# Insert norm2 beside norm1, with the correct 2048 dimension.
anchor = "        self.scale = 256 ** -0.5"
assert s.count(anchor) == 1, "Scale initialization not found uniquely"

s = s.replace(
    anchor,
    """        self.norm2 = RMSNorm(
            2048,
            dtype=dtype,
            eps=1e-6,
        )
""" + anchor,
    1,
)

old_ff = "        ff1 = ff[..., :1024]"
assert s.count(old_ff) == 1, "FF split not found uniquely"

s = s.replace(
    old_ff,
    "        ff = self.norm2(ff)\n" + old_ff,
    1,
)

compile(s, str(p), "exec")
p.write_text(s)
print("NORM2 ADDED - SYNTAX CLEAN")
PY
