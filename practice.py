python3 -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
packages = ["cta_max", "cta_native_batch2_release_candidate/maxserve_cta_extension"]
missing = set()
old_paths = []
checked = 0

for folder in packages:
    base = root / folder
    assert base.is_dir(), f"STOP: missing {base}"

    for p in sorted(base.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        checked += 1
        tree = ast.parse(p.read_text(), filename=str(p))

        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [x.name for x in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                modules = [node.module or ""]

            for module in modules:
                if module.startswith("cta_max.") or module.startswith("maxserve_cta_extension."):
                    pkg, relative = module.split(".", 1)
                    pkgdir = root / ("cta_max" if pkg == "cta_max" else packages[1])
                    q = pkgdir / relative.replace(".", "/")
                    if not q.with_suffix(".py").is_file() and not (q / "__init__.py").is_file():
                        missing.add(module)

            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                if any(x in s for x in (
                    "/application1/CTA_MAX_TRUE_BATCH2_DEV_",
                    "/application1/cta_max_true_batch_dev_",
                    "/application1/CTA_MAX_TRUE_BATCH2_",
                    "/batch2/"
                )):
                    old_paths.append((p.name, node.lineno, s[:140]))

print("PYTHON FILES CHECKED:", checked)
print("MISSING LOCAL IMPORTS:", len(missing))
for x in sorted(missing):
    print("MISSING:", x)

print("DEVELOPMENT PATH REFERENCES:", len(old_paths))
for name, line, value in old_paths[:25]:
    print(f"{name}:{line}: {value}")

print("ORIGINAL FILES: UNCHANGED")
print("READ-ONLY CHECK COMPLETE")
PY
