python3 - <<'PY'
from pathlib import Path
import ast
import shutil
from datetime import datetime

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max_branch_diag.py")
post = Path("artifacts/v1.168-max/cta_max/sequence_postprocess_max.py")

s = p.read_text()
t = post.read_text()

assert s.count("seq_raw = postprocess(sx2)") == 1, "STOP: graph changed"
assert t.count("x = self.seq_dense(x)") == 1, "STOP: postprocess changed"
assert "return x * ops.rsqrt(variance2 + 1e-6) * g2" in t, "STOP: final norm changed"

lines = s.splitlines(keepends=True)
matches = [
    i for i, line in enumerate(lines)
    if line.strip().startswith("seq = ops.matmul(seq_raw,")
    and "seq_w.T" in line
    and "seq_b" in line
]
assert len(matches) == 1, f"STOP: expected one extra dense, found {len(matches)}"

i = matches[0]
indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
lines[i] = indent + "seq = seq_raw\n"

updated = "".join(lines)
ast.parse(updated)

backup = p.with_name(
    p.name + ".before_double_dense_fix_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak"
)
shutil.copy2(p, backup)
p.write_text(updated)

print("EXTRA SEQ_DENSE REMOVED")
print("PYTHON SYNTAX PASS")
print("ORIGINAL DS CODE UNCHANGED")
print("BACKUP:", backup)
PY
