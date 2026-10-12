python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_layer1_ff.py")
s = p.read_text()
tree = ast.parse(s)
lines = s.splitlines()

returns = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Return)
    and "diagnostic: after norm2" in lines[n.lineno - 1]
]
assert len(returns) == 1, f"STOP: diagnostic returns found={len(returns)}"

r = returns[0]
expr = ast.unparse(r.value)

norm_assignments = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "ff" for t in n.targets)
    and "ops.rsqrt" in ast.unparse(n.value)
    and "norm2_g" in ast.unparse(n.value)
    and n.lineno < r.lineno
]

print("ACTUAL RETURN:", expr)
print("PRIOR FF NORMALIZATION:", len(norm_assignments))

if expr == "ff":
    print("ALREADY CORRECT — NO CHANGE")
elif len(norm_assignments) == 1 and "ops.rsqrt" in expr and "norm2_g" in expr:
    indent = lines[r.lineno - 1][:len(lines[r.lineno - 1]) - len(lines[r.lineno - 1].lstrip())]
    lines[r.lineno - 1] = indent + "return ff  # diagnostic: after norm2"
    updated = "\n".join(lines) + "\n"
    ast.parse(updated)
    p.write_text(updated)
    print("DOUBLE NORMALIZATION FIXED")
else:
    print("STOP — DIFFERENT EXPRESSION; NO CHANGE")
PY
