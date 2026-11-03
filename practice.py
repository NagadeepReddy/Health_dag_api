cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

root = Path("artifacts/v1.472-max/pzaas_max")
p = root / "sequence_postprocess_max.py"
manifest = json.loads(
    (root / "pzaas_base_weights/manifest.json").read_text()
)

mapping = {
    "out_norm1_g.npy": "sequence_transformer.out_norm1.g",
    "out_norm2_g.npy": "sequence_transformer.out_norm2.g",
}

source = p.read_text()
tree = ast.parse(source)
changes = []

for filename, key in mapping.items():
    entry = manifest.get(key)
    if not entry:
        raise SystemExit(f"STOP: Missing weight {key}")

    if tuple(entry["shape"]) != (256,):
        raise SystemExit(f"STOP: Shape mismatch {key}")

    if not (root / "pzaas_base_weights" / entry["file"]).is_file():
        raise SystemExit(f"STOP: Missing file {key}")

    matches = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        if not (
            isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "np"
            and n.func.attr == "load"
        ):
            continue
        if not n.args:
            continue
        arg = n.args[0]
        if (
            isinstance(arg, ast.BinOp)
            and isinstance(arg.op, ast.Add)
            and isinstance(arg.left, ast.Name)
            and arg.left.id == "base"
            and isinstance(arg.right, ast.Constant)
            and arg.right.value == filename
        ):
            matches.append(n)

    if len(matches) != 1:
        raise SystemExit(f"STOP: Unexpected load count for {filename}")

    old = ast.get_source_segment(source, matches[0])
    new = f'load_weight("{key}", (256,))'
    if source.count(old) != 1:
        raise SystemExit(f"STOP: Non-unique expression {filename}")
    changes.append((old, new))

for old, new in changes:
    source = source.replace(old, new, 1)

import_line = "from pzaas_max.pzaas_weight_loader import load_weight\n"
if import_line not in source:
    parsed = ast.parse(source)
    lines = source.splitlines(keepends=True)
    pos = 0
    for n in parsed.body:
        if (
            isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str)
            and n is parsed.body[0]
        ):
            pos = n.end_lineno
        elif isinstance(n, ast.ImportFrom) and n.module == "__future__":
            pos = n.end_lineno
    lines.insert(pos, import_line)
    source = "".join(lines)

compile(source, str(p), "exec")
p.write_text(source)

print("PZAAS SEQUENCE POSTPROCESS WIRING: PASS")
print("out_norm1.g: PZAAS")
print("out_norm2.g: PZAAS")
print("SYNTAX: PASS")
print("OTHER GRAPH MODULES: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
