python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

marker="        self.scale = 256 ** -0.5\n"

assert marker in s, "Expected self.scale line not found"
assert "self.norm1 = RMSNorm(" not in s, "self.norm1 already exists"

insert = """        self.norm1 = RMSNorm(
            256,
            dtype=dtype,
            eps=1e-6,
        )
"""

s=s.replace(marker, marker + insert)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER NORM1 MODULE RESTORED")
PY
