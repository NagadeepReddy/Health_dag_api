python - <<'PY'
from pathlib import Path
import ast
import re

p = Path(
    "artifacts/v1.168-max/cta_max/att_pooling_max.py"
)

s = p.read_text()

assert "self.heads = 1" in s, \
    "STOP: attention head configuration differs"

assert "[256, 256, 256, 2048]" in s, \
    "STOP: previously corrected split missing"

updated = s

for name in ("q", "k", "v"):
    pattern = (
        rf'\b{name}\.reshape\('
        rf'{name}\.shape\[0\],\s*2,\s*'
        rf'{name}\.shape\[1\],\s*256\)'
    )

    replacement = (
        f"{name}.reshape("
        f"{name}.shape[0], self.heads, "
        f"{name}.shape[1], 256)"
    )

    updated, count = re.subn(
        pattern, replacement, updated
    )

    assert count == 1, \
        f"STOP: expected one {name} reshape, found {count}"

ast.parse(updated)

p.write_text(updated)

print("Q/K/V HEAD RESHAPES CORRECTED")
print("HEAD COUNT: 1")
print("FUSED SPLIT: 2816")
print("SYNTAX PASS")
print("ORIGINAL TRANSFORMER AND DS CODE UNCHANGED")
PY
