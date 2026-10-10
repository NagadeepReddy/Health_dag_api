python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block.py")
s = p.read_text()

old = "ops.mean(x * x, axis=-1, keepdims=True)"
new = "ops.unsqueeze(ops.mean(x * x, axis=-1), axis=-1)"

old_ff = "ops.mean(ff * ff, axis=-1, keepdims=True)"
new_ff = "ops.unsqueeze(ops.mean(ff * ff, axis=-1), axis=-1)"

assert s.count(old) == 1, "Expected one norm1 expression"
assert s.count(old_ff) == 1, "Expected one norm2 expression"

s = s.replace(old, new, 1)
s = s.replace(old_ff, new_ff, 1)

compile(s, str(p), "exec")
p.write_text(s)

print("RMSNORM MEAN FIX APPLIED - SYNTAX CLEAN")
PY
