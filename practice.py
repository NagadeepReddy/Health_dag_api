cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

root = Path("artifacts/v1.472-max/pzaas_max")
p = root / "att_pooling_max.py"
manifest = json.loads((root / "pzaas_base_weights/manifest.json").read_text())
source = p.read_text()
tree = ast.parse(source)

names = ("att_pooling.norm1.g", "att_pooling.norm2.g")

for name in names:
    entry = manifest.get(name)
    if not entry:
        raise SystemExit(f"STOP: Missing PZAAS tensor {name}")
    if not (root / "pzaas_base_weights" / entry["file"]).is_file():
        raise SystemExit(f"STOP: Missing exported file {name}")

changes = []
for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    f = node.func
    if not (isinstance(f, ast.Attribute) and f.attr == "load"
            and isinstance(f.value, ast.Name) and f.value.id == "np"):
        continue
    if not node.args or not isinstance(node.args[0], ast.Constant):
        continue
    path = node.args[0].value
    if not isinstance(path, str):
        continue
    for name in names:
        if path.endswith("/" + name + ".npy"):
            if "v1.168-max/cta_max/" not in path:
                raise SystemExit("STOP: Unexpected weight source")
            old = ast.get_source_segment(source, node)
            shape = tuple(manifest[name]["shape"])
            changes.append((old, f'load_weight("{name}", {shape})', name))

if len(changes) == 0 and all(
    f'load_weight("{n}"' in source for n in names
):
    print("PZAAS ATTENTION WIRING: ALREADY DONE")
    raise SystemExit(0)

if len(changes) != 2 or {x[2] for x in changes} != set(names):
    raise SystemExit("STOP: Expected exactly two CTA attention loads")

for old, new, _ in changes:
    if source.count(old) != 1:
        raise SystemExit("STOP: Non-unique load expression")
    source = source.replace(old, new, 1)

import_line = "from pzaas_max.pzaas_weight_loader import load_weight\n"
if import_line not in source:
    lines = source.splitlines(keepends=True)
    first = tree.body[0] if tree.body else None
    pos = first.end_lineno if (
        isinstance(first, ast.Expr) and
        isinstance(first.value, ast.Constant) and
        isinstance(first.value.value, str)
    ) else 0
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            pos = max(pos, node.end_lineno)
    lines.insert(pos, import_line)
    source = "".join(lines)

compile(source, str(p), "exec")
p.write_text(source)

print("PZAAS ATTENTION WEIGHT WIRING: PASS")
print("norm1.g: PZAAS")
print("norm2.g: PZAAS")
print("SYNTAX: PASS")
print("OTHER MODULES: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
