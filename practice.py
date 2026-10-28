cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import os

repo = Path.cwd()
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
target = candidate / "grecbase_integration_weights"
filename = "att_pooling.rotary_emb.inv_freq.npy"

assert candidate.is_dir(), "STOP: Batch candidate missing"

matches = sorted(
    (repo / "artifacts/v1.168-max").rglob(filename)
)

print("EXISTING ROTARY EXPORTS:", len(matches))
for p in matches:
    print("SOURCE:", p)

valid = [
    p for p in matches
    if p.parent.name == "grecbase_integration_weights"
    and p.stat().st_size > 0
    and p.open("rb").read(6) == b"\x93NUMPY"
]

assert len(valid) == 1, (
    "STOP: Cannot identify exactly one valid original weight directory"
)

source = valid[0].parent
files = list(source.glob("*.npy"))

assert len(files) >= 1, "STOP: No exported NPY weights"

container_source = "/workspace/" + source.relative_to(repo).as_posix()

if target.is_symlink():
    assert os.readlink(target) == container_source, \
        "STOP: Existing link points somewhere else"
    print("BATCH WEIGHT LINK: ALREADY CORRECT")
else:
    assert not target.exists(), \
        "STOP: Candidate already contains a weight directory"
    os.symlink(container_source, target)
    print("BATCH WEIGHT LINK: CREATED")

print("EXPORTED WEIGHT FILES:", len(files))
print("ROTARY EXPORT: FOUND")
print("CONTAINER WEIGHT PATH:", container_source)
print("WORKING MODEL: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
