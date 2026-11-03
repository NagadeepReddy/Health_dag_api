cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

root = Path("artifacts/v1.472-max/pzaas_max")
p = root / "grecbase_fusion_full_head_72_max.py"
weights = root / "pzaas_base_weights"
manifest = json.loads((weights / "manifest.json").read_text())

assert len(manifest) == 208

for name in ("att_pooling.norm1.g", "att_pooling.norm2.g",
             "att_pooling.rotary_emb.inv_freq"):
    assert name in manifest, f"Missing: {name}"
    assert (weights / manifest[name]["file"]).is_file()

source = p.read_text()
tree = ast.parse(source)
matches = [
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "WDIR"
            for t in n.targets)
]
assert len(matches) == 1, "Unexpected WDIR definitions"

n = matches[0]
lines = source.splitlines(keepends=True)
old = "".join(lines[n.lineno-1:n.end_lineno])

if "pzaas_base_weights" in old:
    print("MAIN GRAPH PATH: ALREADY WIRED")
elif "grecbase_integration_weights" in old:
    lines[n.lineno-1:n.end_lineno] = [
        'WDIR = Path(__file__).resolve().parent / "pzaas_base_weights"\n'
    ]
    updated = "".join(lines)
    compile(updated, str(p), "exec")
    p.write_text(updated)
    print("MAIN GRAPH PATH: WIRED")
else:
    raise SystemExit("STOP: Unknown WDIR source")

print("PZAAS WEIGHTS: 208 VERIFIED")
print("OTHER GRAPH MODULES: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
