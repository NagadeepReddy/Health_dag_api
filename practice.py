python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/att_pooling_max.py")
s = p.read_text()

old = "[512, 256, 256, 2048]"
new = "[256, 256, 256, 2048]"

assert s.count(old) == 1, \
    "STOP: expected attention split not found uniquely"

updated = s.replace(old, new, 1)
ast.parse(updated)

assert sum([256, 256, 256, 2048]) == 2816
assert "self.fused_dims = (256, 256, 256, 2048)" in updated, \
    "STOP: configured dimensions differ"

p.write_text(updated)

print("ATTENTION SPLIT CORRECTED")
print("SPLIT TOTAL: 2816")
print("SYNTAX PASS")
print("ORIGINAL TRANSFORMER AND DS CODE UNCHANGED")
PY
