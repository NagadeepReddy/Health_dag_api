
python3 -B - <<'PY'
from pathlib import Path
import ast
import hashlib

dev = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max")

assert dev.is_dir() and clean.is_dir(), "STOP: Package missing"

pending = list(clean.glob("*.py"))
seen = set()
needed = {}

while pending:
    p = pending.pop()
    if p in seen:
        continue
    seen.add(p)

    tree = ast.parse(p.read_bytes(), filename=str(p))
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("cta_max."):
                    imports.add(a.name.split(".")[1])

        elif isinstance(node, ast.ImportFrom):
            if node.module == "cta_max" or (node.level and not node.module):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif node.module and node.module.startswith("cta_max."):
                imports.add(node.module.split(".")[1])
            elif node.level and node.module:
                imports.add(node.module.split(".")[0])

    for name in imports:
        target = clean / (name + ".py")
        source = dev / (name + ".py")

        if not target.exists() and source.is_file() and name not in needed:
            needed[name] = source
            pending.append(source)

print("=== REQUIRED IMPORT CLOSURE ===")
for name in sorted(needed):
    print("REQUIRED:", name)

assert len(needed) <= 25, "STOP: Too many dependencies; review before copying"

for name, source in sorted(needed.items()):
    target = clean / (name + ".py")
    data = source.read_bytes()
    ast.parse(data, filename=str(source))

    with target.open("xb") as f:
        f.write(data)

    assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(data).digest()
    print("COPIED AND VERIFIED:", name)

print("REQUIRED MODULES COPIED:", len(needed))
print("ORIGINAL CTA: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
