python3 -B - <<'PY'
from pathlib import Path
import ast

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max")

pending = ["live_cta_pipeline_bridge", "run_live_max_inference"]
seen = set()
missing = set()

while pending:
    name = pending.pop()
    if name in seen:
        continue
    seen.add(name)

    source = repo / (name.replace(".", "/") + ".py")
    target = clean / (name.replace(".", "/") + ".py")

    if not target.is_file():
        missing.add(name)

    if not source.is_file():
        print("SOURCE NOT FOUND:", name)
        continue

    tree = ast.parse(source.read_text())
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [x.name for x in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            modules = [node.module or ""]

        for module in modules:
            if module.startswith("cta_max."):
                pending.append(module[len("cta_max."):])

print("LOCAL MODULES CHECKED:", len(seen))
print("MISSING FROM CLEAN PACKAGE:")
for name in sorted(missing):
    print(" ", name)
print("READ-ONLY CHECK COMPLETE")
PY
