python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
"""        norm1_g = self.norm1_g
        x_norm = x_norm * norm1_g
""",
"""        x_norm = self.norm1(x)
"""
)

with open(p, "w") as f:
    f.write(s)

print("STALE NORM1_G REPLACED WITH RMSNORM MODULE")
PY
