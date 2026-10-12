python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/context_head_base_max.py")
original = p.read_text()
lines = original.splitlines(keepends=True)

matches = [
    i for i, line in enumerate(lines)
    if line.strip() == "extracted = ops.squeeze(extracted, axis=1)"
]

assert len(matches) == 1, f"STOP: found {len(matches)} squeeze lines"
assert any(
    line.strip() == "return ctx_out, extracted"
    for line in lines
), "STOP: return differs"

del lines[matches[0]]

updated = "".join(lines)
ast.parse(updated)
p.write_text(updated)

print("ADAPTER CORRECTED — SYNTAX OK")
print("ORIGINAL MAX COMPONENTS AND DS CODE UNCHANGED")
PY
