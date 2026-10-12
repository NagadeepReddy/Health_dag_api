python - <<'PY'
from pathlib import Path
import ast

b = Path("artifacts/v1.168-max/cta_max")

combined = b / "context_head_combined.py"
full = b / "context_head_full.py"

assert combined.is_file() and full.is_file()

s1 = combined.read_text()
s2 = full.read_text()

old1 = "return ops.concat([wide_out, deep_out], axis=1)"
new1 = "return ops.concat([deep_out, wide_out], axis=1)"

old2 = "return self.combine(deep_out, wide_out)"
new2 = "return ops.concat([deep_out, wide_out], axis=1)"

assert s1.count(old1) == 1, "STOP: combined code differs"
assert s2.count(old2) == 1, "STOP: full code differs"

s1 = s1.replace(old1, new1, 1)
s2 = s2.replace(old2, new2, 1)

tree = ast.parse(s2)
has_ops = any(
    isinstance(n, ast.ImportFrom)
    and n.module == "max.graph"
    and any(a.name == "ops" for a in n.names)
    for n in tree.body
)

if not has_ops:
    future = [
        n.end_lineno for n in tree.body
        if isinstance(n, ast.ImportFrom)
        and n.module == "__future__"
    ]
    lines = s2.splitlines()
    lines.insert(max(future, default=0), "from max.graph import ops")
    s2 = "\n".join(lines) + "\n"

ast.parse(s1)
ast.parse(s2)

combined.write_text(s1)
full.write_text(s2)

print("CONTEXTHEAD CONCAT ORDER CORRECTED")
print("UNDEFINED COMBINE CALL REMOVED")
print("SYNTAX OK")
print("TRANSFORMER AND DS CODE UNCHANGED")
PY
