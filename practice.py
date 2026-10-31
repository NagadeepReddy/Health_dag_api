python3 -B - <<'PY'
from pathlib import Path
import hashlib
import shutil
import ast

src = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
dst = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max")

names = [
    "__init__.py",
    "live_cta_pipeline_bridge.py",
    "run_live_max_inference.py",
]

assert src.is_dir() and dst.is_dir(), "STOP: Package directory missing"
assert not dst.is_symlink(), "STOP: Destination is a symlink"

for name in names:
    original = src / name
    target = dst / name

    assert original.is_file(), f"STOP: Original missing: {name}"
    assert not original.is_symlink(), f"STOP: Source symlink: {name}"

    data = original.read_bytes()
    if target.exists():
        assert target.is_file() and target.read_bytes() == data, \
            f"STOP: Existing clean file differs: {name}"
        print("ALREADY IDENTICAL:", name)
    else:
        with target.open("xb") as out:
            out.write(data)
        assert target.read_bytes() == data
        print("COPIED AND VERIFIED:", name,
              hashlib.sha256(data).hexdigest()[:16])

print("\n=== CHECK LOCAL CTA IMPORTS ===")
missing = set()

for name in names:
    tree = ast.parse((dst / name).read_text())
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [x.name for x in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            modules = [node.module or ""]

        for module in modules:
            if module.startswith("cta_max."):
                relative = module.removeprefix("cta_max.").replace(".", "/")
                if not ((dst / (relative + ".py")).is_file()
                        or (dst / relative / "__init__.py").is_file()):
                    missing.add(module)

print("MISSING LOCAL MODULES:", sorted(missing))
print("ORIGINAL FILES: UNCHANGED")
print("CLEAN PACKAGE CHECK COMPLETE")
PY
