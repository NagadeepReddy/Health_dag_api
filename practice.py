cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
src = p.read_text()
lines = src.splitlines(keepends=True)

starts = [
    i for i, line in enumerate(lines)
    if line.strip() == "seq_raw = postprocess(sx2)"
]
ends = [
    i for i, line in enumerate(lines)
    if line.strip() == "sibling_outputs = []"
]

assert len(starts) == 1, "STOP: Sequence start not unique"
assert len(ends) == 1, "STOP: Sibling boundary not unique"

a, b = starts[0], ends[0]
assert a < b and b - a <= 15, "STOP: Unexpected block"

indent = lines[a][:len(lines[a]) - len(lines[a].lstrip())]
sibling_indent = lines[b][:len(lines[b]) - len(lines[b].lstrip())]

assert indent == sibling_indent, "STOP: Indentation differs"

block = "".join(lines[a:b])

for token in (
    "seq_w =",
    "seq_b =",
    "assert seq_w.shape",
    "assert seq_b.shape",
    "seq = ops.matmul(seq_raw",
):
    assert token in block, f"STOP: Missing {token}"

new_lines = (
    lines[:a]
    + [indent + "seq = postprocess(sx2)\n"]
    + lines[b:]
)

new_src = "".join(new_lines)

ast.parse(new_src)

backup = p.with_name(p.name + ".before_duplicate_seq_dense_fix")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(new_src)

print("FIX APPLIED")
print("Duplicate Sequence projection removed")
print("Sibling code preserved")
print("Python syntax PASS")
print("Backup:", backup)
PY
