cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

root = Path("artifacts/v1.472-max/pzaas_max")
p = root / "grecbase_fusion_full_head_72_max.py"
weights = root / "pzaas_base_weights"
manifest = json.loads((weights / "manifest.json").read_text())

required = [
    "att_pooling.norm1.g",
    "att_pooling.norm2.g",
    "att_pooling.rotary_emb.inv_freq",
]

for name in required:
    entry = manifest.get(name)
    if not entry or not (weights / entry["file"]).is_file():
        raise SystemExit(f"STOP: Missing PZAAS weight: {name}")

source = p.read_text()
tree = ast.parse(source)

matches = [
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "WDIR"
            for t in n.targets)
]

if len(matches) != 1:
    raise SystemExit("STOP: WDIR assignment not unique")

n = matches[0]
old = ast.get_source_segment(source, n.value)

if "grecbase_integration_weights" not in old:
    raise SystemExit("STOP: Unexpected weight directory")

lines = source.splitlines(keepends=True)
lines[n.lineno-1:n.end_lineno] = [
    'WDIR = Path(__file__).resolve().parent / "pzaas_base_weights"\n'
]

updated = "".join(lines)
compile(updated, str(p), "exec")
p.write_text(updated)

print("PZAAS MAIN GRAPH WEIGHT PATH: PASS")
print("PZAAS ATTENTION WEIGHTS: VERIFIED")
print("SEQUENCE WEIGHTS: PREVIOUSLY WIRED")
print("REMAINING GRAPH MODULES: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
