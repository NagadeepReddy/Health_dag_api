python3 -B - <<'PY'
from pathlib import Path
import ast, hashlib

roots = {
    "OCT28": Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"),
    "OCT29": Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/cta_max"),
}

for name in ("run_real_sanity_input_adapter.py", "grecbase_fusion_full_head_72_max.py"):
    print("\n=== MODULE:", name, "===")
    for label, root in roots.items():
        p = root / name
        if not p.is_file():
            print(label, "MISSING")
            continue
        source = p.read_bytes()
        print(label, "SHA256:", hashlib.sha256(source).hexdigest())
        tree = ast.parse(source, filename=str(p))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
        print("IMPORTS:", ", ".join(sorted(imports)))

print("\nREAD-ONLY CHECK COMPLETE")
PY
