python3 -B - <<'PY'
from pathlib import Path
import hashlib
import shutil

src = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
parent = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
dst = parent / "cta_max"

names = [
    "__init__.py",
    "live_cta_pipeline_bridge.py",
    "run_live_max_inference.py",
]

assert src.is_dir() and not src.is_symlink(), "STOP: Original package invalid"
assert parent.is_dir() and not parent.is_symlink(), "STOP: Clean parent missing"
assert not dst.is_symlink(), "STOP: Clean package is a symlink"

for name in names:
    assert (src / name).is_file(), f"STOP: Original missing: {name}"

dst.mkdir(exist_ok=True)

for name in names:
    source = src / name
    target = dst / name

    if target.exists():
        assert target.is_file(), f"STOP: Invalid destination: {name}"
        assert source.read_bytes() == target.read_bytes(), \
            f"STOP: Existing file differs: {name}"
        print("ALREADY IDENTICAL:", name)
    else:
        with target.open("xb") as f:
            f.write(source.read_bytes())

        assert hashlib.sha256(source.read_bytes()).digest() == \
               hashlib.sha256(target.read_bytes()).digest()
        print("COPIED AND VERIFIED:", name)

print("CLEAN PACKAGE DIRECTORY: PASS")
print("ORIGINAL FILES: UNCHANGED")
print("NEXT: VERIFY DEPENDENCIES BEFORE HTTP TEST")
PY
