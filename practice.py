python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")

changes = [
    (
        base / "models_raw_attn_diagnostic.py",
        "return self.ff_out(ff)  # diagnostic: ff_out only",
        "return ff  # diagnostic: after norm2",
    ),
    (
        base / "parallel_transformer_block_layer1_ff.py",
        "return self.ff_out(swiglu)  # diagnostic: ff_out after norm2",
        "return ff  # diagnostic: after norm2",
    ),
]

prepared = []
for path, old, new in changes:
    original = path.read_text()
    count = original.count(old)
    assert count == 1, f"STOP: {path.name}: found {count} matching returns"
    updated = original.replace(old, new, 1)
    ast.parse(updated)
    prepared.append((path, original, updated))

for path, original, updated in prepared:
    backup = path.with_suffix(".before_norm2_compare.bak")
    assert not backup.exists(), f"STOP: backup exists: {backup}"

for path, original, updated in prepared:
    path.with_suffix(".before_norm2_compare.bak").write_text(original)
    path.write_text(updated)
    print("READY:", path.name)

print("BLOCK-1 NORM2 COMPARISON PREPARED")
print("REAL MAX BLOCK AND DS CODE UNCHANGED")
PY
