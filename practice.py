cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

src = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
dst = Path("artifacts/v1.472-max/pzaas_max")

pending = ["grecbase_fusion_full_head_72_max.py"]
files = {}

while pending:
    name = pending.pop()
    if name in files:
        continue
    p = src/name
    if not p.is_file():
        raise SystemExit(f"MISSING: {p}")

    text = p.read_text()
    tree = ast.parse(text)
    files[name] = text

    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(x.name for x in node.names)

        for mod in modules:
            if mod.startswith("cta_max."):
                dep = mod[len("cta_max."):].replace(".", "/") + ".py"
                if (src/dep).is_file() and dep not in files:
                    pending.append(dep)

targets = [dst/name for name in files]
targets.append(dst/"__init__.py")
existing = [str(p) for p in targets if p.exists()]
if existing:
    raise SystemExit(f"STOP: Existing files: {existing}")

for name, text in sorted(files.items()):
    text = text.replace("cta_max.", "pzaas_max.")
    target = dst/name
    ast.parse(text)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    print("CREATED:", name)

(dst/"__init__.py").write_text("")
print("\nPZAAS GRAPH SOURCE: PREPARED")
print("PYTHON FILES:", len(files))
print("PZAAS WEIGHT/DIMENSION ADAPTATION: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
