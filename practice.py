python - <<'PY'
import ast

p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

# Syntax
ast.parse(s)

checks = {
    "RMSNorm imported": "RMSNorm" in s,
    "norm1 initialized": "self.norm1 = RMSNorm(" in s,
    "norm1 used": "self.norm1(x)" in s,
    "stale norm1_g absent": "norm1_g" not in s,
    "stale norm2_g absent": "norm2_g" not in s,
    "keepdims absent": "keepdims" not in s,
    "fused projection present": "fused_attn_ff_proj" in s,
    "attention output present": "attn_out" in s,
    "FF output present": "ff_out" in s,
}

for k,v in checks.items():
    print(f"{k}: {'OK' if v else 'FAIL'}")

assert all(checks.values()), "STRUCTURE CHECK FAILED"

print("TRANSFORMER BLOCK STRUCTURE CLEAN")
PY
