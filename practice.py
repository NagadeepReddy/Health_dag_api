cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import os

repo = Path.cwd()
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
target = candidate / "sibling_context_weights"
filename = "sibling_context_head_deep_embedding_0.weight.npy"

assert candidate.is_dir(), "STOP: Batch candidate missing"

matches = sorted(
    (repo / "artifacts/v1.168-max").rglob(filename)
)

print("EXISTING SIBLING WEIGHTS:", len(matches))

valid = [
    p for p in matches
    if p.parent.name == "sibling_context_weights"
    and p.is_file()
    and p.stat().st_size > 6
    and p.open("rb").read(6) == b"\x93NUMPY"
]

assert len(valid) == 1, \
    "STOP: Cannot uniquely locate the exported sibling weights"

source = valid[0].parent
container_source = "/workspace/" + source.relative_to(repo).as_posix()

if target.is_symlink():
    assert os.readlink(target) == container_source, \
        "STOP: Existing sibling link differs"
    print("SIBLING WEIGHT LINK: ALREADY CORRECT")
else:
    assert not target.exists(), \
        "STOP: Existing sibling directory must be preserved"
    os.symlink(container_source, target)
    print("SIBLING WEIGHT LINK: CREATED")

print("SIBLING WEIGHT FILES:", len(list(source.glob("*.npy"))))
print("SOURCE:", source)
print("CONTAINER PATH:", container_source)
print("DS CODE: UNCHANGED")
print("WORKING HTTP 200: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
