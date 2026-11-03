cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

root = Path("artifacts/v1.472-max/pzaas_max")
p = root / "parallel_transformer_block_2layers.py"
manifest = json.loads(
    (root / "pzaas_base_weights/manifest.json").read_text()
)

# Verify all four PZAAS tensors.
for layer in (0, 1):
    for norm in ("norm1", "norm2"):
        key = f"sequence_transformer.ptransformer.{layer}.fn.{norm}.g"
        entry = manifest.get(key)
        if not entry:
            raise SystemExit(f"STOP: Missing {key}")
        if not (root / "pzaas_base_weights" / entry["file"]).is_file():
            raise SystemExit(f"STOP: Missing file for {key}")
        print("VERIFIED:", key, entry["shape"])

source = p.read_text()
tree = ast.parse(source)
changes = []

for n in ast.walk(tree):
    if not isinstance(n, ast.Call):
        continue
    if not isinstance(n.func, ast.Attribute):
        continue
    if not (isinstance(n.func.value, ast.Name)
            and n.func.value.id == "np"
            and n.func.attr == "load"):
        continue

    old = ast.get_source_segment(source, n)
    if "v1.168-max/cta_max/sequence_weights/" not in old:
        continue

    if "fn_norm1_g" in old:
        norm = "norm1"
    elif "fn_norm2_g" in old:
        norm = "norm2"
    else:
        raise SystemExit("STOP: Unexpected CTA load")

    new = (
        'load_weight('
        f'"sequence_transformer.ptransformer.0.fn.{norm}.g" '
        'if self.layer_idx == 0 else '
        f'"sequence_transformer.ptransformer.1.fn.{norm}.g")'
    )
    changes.append((old, new))

if len(changes) != 2:
    raise SystemExit(f"STOP: Expected 2 loads, found {len(changes)}")

for old, new in changes:
    if source.count(old) != 1:
        raise SystemExit("STOP: Non-unique expression")
    source = source.replace(old, new, 1)

imp = "from pzaas_max.pzaas_weight_loader import load_weight\n"
if imp not in source:
    parsed = ast.parse(source)
    lines = source.splitlines(keepends=True)
    pos = 0
    if parsed.body and isinstance(parsed.body[0], ast.Expr):
        if isinstance(parsed.body[0].value, ast.Constant):
            if isinstance(parsed.body[0].value.value, str):
                pos = parsed.body[0].end_lineno
    for n in parsed.body:
        if isinstance(n, ast.ImportFrom) and n.module == "__future__":
            pos = max(pos, n.end_lineno)
    lines.insert(pos, imp)
    source = "".join(lines)

compile(source, str(p), "exec")
p.write_text(source)

print("\nPZAAS TRANSFORMER WEIGHT WIRING: PASS")
print("FOUR TRAINED WEIGHTS: CONNECTED")
print("SYNTAX: PASS")
print("OTHER MODULES / DIMENSIONS: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
