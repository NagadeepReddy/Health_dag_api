cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

r = Path("artifacts/v1.472-max/pzaas_max")
p = r / "sequence_postprocess_max.py"
s = p.read_text()
tree = ast.parse(s)

assigns = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Assign)
    and len(n.targets) == 1
    and isinstance(n.targets[0], ast.Name)
    and n.targets[0].id == "base"
]
uses = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Name)
    and n.id == "base"
    and isinstance(n.ctx, ast.Load)
]

if len(assigns) == 1 and not uses:
    n = assigns[0]
    old = ast.get_source_segment(s, n)
    if "v1.168-max/cta_max/sequence_weights/" not in old:
        raise SystemExit("STOP: Unexpected base path")
    lines = s.splitlines(keepends=True)
    del lines[n.lineno-1:n.end_lineno]
    updated = "".join(lines)
    compile(updated, str(p), "exec")
    p.write_text(updated)
    print("UNUSED CTA PATH: REMOVED")
elif not assigns and not uses:
    print("UNUSED CTA PATH: ALREADY REMOVED")
else:
    raise SystemExit("STOP: base may still be required")

files = sorted(r.glob("*.py"))
for f in files:
    compile(f.read_text(), str(f), "exec")

legacy = [
    f"{f.name}:{i}"
    for f in files
    for i, line in enumerate(f.read_text().splitlines(), 1)
    if "v1.168" in line or "cta_max/" in line
]

print("GRAPH SYNTAX: PASS")
print("LEGACY CTA PATHS:", legacy)

m = json.loads(
    (r/"pzaas_base_weights/manifest.json").read_text()
)
print("\n=== PZAAS DIMENSION REFERENCES ===")
for key in (
    "sequence_transformer.item_embedding.weight",
    "sequence_transformer.item_meta_embedding.weight",
    "sequence_transformer.seq_dense.weight",
    "remove_tasks_dense2.weight",
):
    print(key, m[key]["shape"] if key in m else "NOT FOUND")

print("\n=== REMAINING DIMENSION-SENSITIVE CODE ===")
terms = ("10727", "10819", "523", "451", "10654")
for f in files:
    for i, line in enumerate(f.read_text().splitlines(), 1):
        if any(t in line for t in terms):
            print(f"{f.name}:{i}: {line.strip()[:130]}")

print("ORIGINAL DS: UNCHANGED")
print("MAX COMPILATION: PENDING")
PY
