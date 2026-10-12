python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
correct = base / "sequence_weights/fn_norm1_g_layer1.npy"
assert correct.is_file(), "STOP: Block-1 norm1 weight missing"

files = [
    base / "run_transformer_layer1.py",
    base / "run_transformer_layer1_ff.py",
]

prepared = []

for p in files:
    s = p.read_text()
    tree = ast.parse(s)

    matches = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        if not isinstance(n.func, ast.Name) or n.func.id != "next":
            continue
        if len(n.args) != 1:
            continue
        g = n.args[0]
        if not isinstance(g, ast.Call):
            continue
        if not isinstance(g.func, ast.Attribute) or g.func.attr != "glob":
            continue
        if len(g.args) == 1 and isinstance(g.args[0], ast.Constant):
            if g.args[0].value == "*norm1*g*.npy":
                matches.append(ast.get_source_segment(s, n))

    assert len(matches) == 1, f"STOP: {p.name}: found {len(matches)} wildcard loaders"

    updated = s.replace(matches[0], f'Path("{correct}")', 1)
    ast.parse(updated)
    prepared.append((p, updated))

for p, updated in prepared:
    p.write_text(updated)
    print("FIXED:", p.name)

print("BLOCK-1 NORM1 PATHS CORRECTED — SYNTAX OK")
print("BLOCK-0 AND DS CODE UNCHANGED")
PY
