cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import os

source = Path.cwd() / "artifacts/v1.168-max/cta_max/sibling_context_weights"
target = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/sibling_context_weights")

assert source.is_dir(), "STOP: Original sibling weights missing"
assert target.parent.is_dir(), "STOP: Batch candidate missing"

files = sorted(source.glob("*.npy"))
assert len(files) == 20, f"STOP: Expected 20 weights, found {len(files)}"

for p in files:
    with p.open("rb") as f:
        assert f.read(6) == b"\x93NUMPY", f"STOP: Invalid weight {p.name}"

container_source = "/workspace/" + source.relative_to(Path.cwd()).as_posix()

if target.is_symlink():
    assert os.readlink(target) == container_source, "STOP: Existing link differs"
    print("SIBLING WEIGHT LINK: ALREADY CORRECT")
else:
    assert not target.exists(), "STOP: Existing candidate directory"
    target.symlink_to(container_source, target_is_directory=True)
    print("SIBLING WEIGHT LINK: CREATED")

print("SIBLING WEIGHT FILES: 20 VALIDATED")
print("SOURCE:", source)
print("CONTAINER TARGET:", container_source)
print("DS CODE: UNCHANGED")
print("WORKING HTTP 200: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
