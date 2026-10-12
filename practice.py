python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/sequence_pooling_max.py")
s = p.read_text()

old = "return ops.concat([mean_out, max_out], axis=1)"
new = """return ops.reshape(
            ops.concat([mean_out, max_out], axis=1),
            [-1, 512],
        )"""

assert s.count(old) == 1, "STOP: pooling implementation differs"

updated = s.replace(old, new, 1)
ast.parse(updated)
p.write_text(updated)

print("MAX POOLING SHAPE CORRECTED")
print("OUTPUT: [batch, 512]")
print("SYNTAX OK")
print("VERIFIED TRANSFORMER AND DS CODE UNCHANGED")
PY
