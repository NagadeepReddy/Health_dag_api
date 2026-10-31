python3 -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
entries = ["run_real_sanity_input_adapter", "grecbase_fusion_full_head_72_max"]
required = set()
missing = set()

def scan(name):
    if name in required:
        return
    path = root / (name.replace(".", "/") + ".py")
    if not path.is_file():
        missing.add(name)
        return
    required.add(name)
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        candidates = []
        if isinstance(node, ast.Import):
            candidates = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            prefix = node.module or ""
            if prefix.startswith("cta_max."):
                candidates = [prefix]
            elif prefix == "cta_max":
                candidates = ["cta_max." + a.name for a in node.names]
            elif node.level:
                candidates = ["cta_max." + prefix] if prefix else []
        for module in candidates:
            if module.startswith("cta_max."):
                local = module.removeprefix("cta_max.")
                if (root / (local.replace(".", "/") + ".py")).is_file():
                    scan(local)

for entry in entries:
    scan(entry)

print("=== REQUIRED CTA_MAX MODULES (STATIC IMPORTS) ===")
for name in sorted(required):
    print(name + ".py")
print("MODULE COUNT:", len(required))
print("UNRESOLVED ENTRY MODULES:", sorted(missing))
print("DYNAMIC IMPORTS STILL REQUIRE REVIEW")
print("READ-ONLY CHECK COMPLETE")
PY
