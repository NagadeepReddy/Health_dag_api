python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")

changes = [
    (
        base / "models_raw_attn_diagnostic.py",
        "return self.ff_out(ff)",
        "return ff  # diagnostic: after norm2",
    ),
    (
        base / "parallel_transformer_block_layer1_ff.py",
        "return self.ff_out(swiglu)",
        "return ff * ops.rsqrt(variance2 + 1e-6) * norm2_g  # diagnostic: after norm2",
    ),
]

prepared = []

for path, old, new in changes:
    original = path.read_text()
    assert original.count(old) == 1, f"STOP: {path.name}: return differs"
    updated = original.replace(old, new, 1)
    ast.parse(updated)
    backup = Path(str(path) + ".pre_layer1_norm2.bak")
    assert not backup.exists(), f"STOP: backup already exists: {backup}"
    prepared.append((path, backup, original, updated))

for path, backup, original, updated in prepared:
    backup.write_text(original)
    path.write_text(updated)
    print("UPDATED:", path.name)

print("BLOCK-1 POST-NORM2 DIAGNOSTICS READY")
print("REAL MAX BLOCK AND DS CODE UNCHANGED")
PY
