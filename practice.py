python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_graph_2layers.py")

s = p.read_text()

old = "output = block1(block0(x, pos_emb), pos_emb)"
new = """x1 = x + block0(x, pos_emb)
    output = x1 + block1(x1, pos_emb)"""

assert s.count(old) == 1, f"STOP: expected one chained call, found {s.count(old)}"

updated = s.replace(old, new, 1)
ast.parse(updated)
p.write_text(updated)

print("TWO-LAYER RESIDUAL CONNECTIONS ADDED")
print("SYNTAX VERIFIED")
print("VERIFIED BLOCKS AND DS CODE UNCHANGED")
PY
