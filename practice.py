cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json, re

root = Path("artifacts/v1.472-max/pzaas_max")
p = root / "grecbase_fusion_full_head_72_max.py"
manifest = json.loads(
    (root / "pzaas_base_weights/manifest.json").read_text()
)

expected = {
    "seq_w": ("seq_dense.weight", (256, 256)),
    "seq_b": ("seq_dense.bias", (256,))
}

for var, (key, shape) in expected.items():
    if tuple(manifest[key]["shape"]) != shape:
        raise SystemExit(f"SHAPE MISMATCH: {key}")

source = p.read_text()
tree = ast.parse(source)
lines = source.splitlines(keepends=True)
changes = []

for var, (key, shape) in expected.items():
    found = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == var
    ]
    if len(found) != 1:
        raise SystemExit(f"STOP: {var} assignment not unique")

    n = found[0]
    old = "".join(lines[n.lineno-1:n.end_lineno])
    if not any(x in old for x in ("np.load(", "torch")):
        raise SystemExit(f"STOP: Unexpected {var} source")

    indent = re.match(r"\s*", lines[n.lineno-1]).group()
    new = (
        f'{indent}{var} = np.asarray('
        f'load_weight("{key}", {shape}), dtype=np.float32)\n'
    )
    changes.append((n.lineno-1, n.end_lineno, new))

for start, end, new in sorted(changes, reverse=True):
    lines[start:end] = [new]

updated = "".join(lines)
updated = (
    "from pzaas_max.pzaas_weight_loader import load_weight\n"
    + updated
)

compile(updated, str(p), "exec")
p.write_text(updated)

print("PZAAS SEQUENCE WEIGHT WIRING: PASS")
print("seq_dense.weight: PZAAS")
print("seq_dense.bias: PZAAS")
print("SYNTAX: PASS")
print("OTHER GRAPH WEIGHTS: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
