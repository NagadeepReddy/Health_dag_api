python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
s = p.read_text()
tree = ast.parse(s)

blocks = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.If)
    and ast.unparse(n.test) == "valid_length is not None"
]

assert len(blocks) == 1, "STOP: mask block not unique"
body = blocks[0].body

def assignment_index(name):
    return [
        i for i, n in enumerate(body)
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == name
    ]

w = assignment_index("scores")
c = assignment_index("causal")

assert len(w) == 2 and len(c) == 1, "STOP: unexpected mask structure"

wi, ci, ai = w[0], c[0], w[1]
assert ci == wi + 1 and ai == ci + 1, "STOP: mask statements differ"
assert ast.unparse(body[wi].value) == "ops.where(positions >= valid, negative, scores)"
assert "np.triu" in ast.unparse(body[ci].value)
assert "causal.reshape" in ast.unparse(body[ai].value)

lines = s.splitlines(keepends=True)
mask_line = body[wi].lineno - 1

assert lines[mask_line].count("positions >= valid") == 1
lines[mask_line] = lines[mask_line].replace(
    "positions >= valid", "positions < valid", 1
)

del lines[body[ci].lineno - 1:body[ai].end_lineno]

updated = "".join(lines)
ast.parse(updated)

backup = p.with_name(
    p.name + ".before_pt_mask_alignment_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak"
)
shutil.copy2(p, backup)
p.write_text(updated)

print("MAX mask aligned with original PyTorch")
print("Extra causal mask removed")
print("Python syntax: PASS")
print("Original DS code: UNCHANGED")
print("Backup:", backup)
PY
