python3 -B - <<'PY'
from pathlib import Path
import ast
import hashlib

src = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
dst = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max")

assert src.is_dir() and dst.is_dir(), "STOP: Package directory missing"

available = {p.stem: p for p in src.glob("*.py")}
pending = list(dst.glob("*.py"))
seen = set()
missing = {}

while pending:
    p = pending.pop()
    if p in seen:
        continue
    seen.add(p)
    tree = ast.parse(p.read_bytes(), filename=str(p))

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("cta_max."):
                names.add(node.module.split(".")[1])
            elif node.level and node.module:
                names.add(node.module.split(".")[0])
            elif node.module == "cta_max":
                names.update(x.name.split(".")[0] for x in node.names)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("cta_max."):
                    names.add(alias.name.split(".")[1])

    for name in names:
        target = dst / (name + ".py")
        if not target.exists() and name in available and name not in missing:
            missing[name] = available[name]
            pending.append(available[name])

assert (dst / "sequence_pooling_max.py").is_file() or "sequence_pooling_max" in missing, \
    "STOP: Required sequence_pooling_max source not found"
assert len(missing) <= 25, "STOP: Too many missing modules; review needed"

for name, source in sorted(missing.items()):
    target = dst / (name + ".py")
    content = source.read_bytes()
    with target.open("xb") as f:
        f.write(content)
    assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(content).digest()
    print("COPIED AND VERIFIED:", name)

print("MISSING IMPORT DEPENDENCIES COPIED:", len(missing))
print("ORIGINAL CTA: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
