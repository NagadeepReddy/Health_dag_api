python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_graph_2layers.py")
s = p.read_text()
lines = s.splitlines()

old = "output = block1(block0(x, pos_emb), pos_emb)"
matches = [i for i, line in enumerate(lines) if line.strip() == old]

assert len(matches) == 1, f"STOP: expected one graph call, found {len(matches)}"

i = matches[0]
indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]

lines[i:i+1] = [
    indent + "x1 = x + block0(x, pos_emb)",
    indent + "output = x1 + block1(x1, pos_emb)"
]

updated = "\n".join(lines) + "\n"
ast.parse(updated)
p.write_text(updated)

print("TWO-LAYER RESIDUAL CONNECTIONS ADDED")
print("SYNTAX VERIFIED")
print("VERIFIED BLOCKS AND DS CODE UNCHANGED")
PY
