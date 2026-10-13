cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast, shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
src = p.read_text()

start = "    seq_raw = postprocess(sx2)"
end = "    sibling_outputs = []"

assert src.count(start) == 1, "STOP: Sequence block not unique"
assert src.count(end) == 1, "STOP: Sibling boundary not unique"

a = src.index(start)
b = src.index(end)
assert a < b, "STOP: Unexpected source order"

block = src[a:b]

for token in (
    "seq_w =",
    "seq_b =",
    "assert seq_w.shape",
    "assert seq_b.shape",
    "seq = ops.matmul(seq_raw",
):
    assert token in block, f"STOP: Missing {token}"

new_src = (
    src[:a]
    + "    seq = postprocess(sx2)\n\n"
    + src[b:]
)

ast.parse(new_src)

backup = p.with_name(p.name + ".before_duplicate_seq_dense_fix")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(new_src)

print("FIX APPLIED: Redundant Sequence projection removed")
print("BACKUP:", backup)
print("SYNTAX: PASS")
PY
