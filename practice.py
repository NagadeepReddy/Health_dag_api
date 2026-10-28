cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import os

repo = Path.cwd()
source_root = repo / "artifacts/v1.168-max/cta_max"
candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
name = "nlp_encoder.embeddings.word_embeddings.weight.npy"

assert source_root.is_dir(), "STOP: Original MAX files missing"
assert candidate.is_dir(), "STOP: Batch candidate missing"

matches = [
    p for p in source_root.rglob(name)
    if p.is_file() and not p.is_symlink()
]

print("EXISTING NLP EXPORT MATCHES:", len(matches))
for p in matches:
    print("FOUND:", p)

assert len(matches) == 1, \
    "STOP: NLP export missing or ambiguous"

source = matches[0].parent
relative = source.relative_to(source_root)
target = candidate / relative

files = sorted(source.glob("*.npy"))
assert files, "STOP: NLP weight directory empty"

for p in files:
    with p.open("rb") as f:
        assert f.read(6) == b"\x93NUMPY", \
            f"STOP: Invalid weight {p.name}"

container_source = (
    "/workspace/artifacts/v1.168-max/cta_max/"
    + relative.as_posix()
)

assert target.parent.is_dir(), \
    "STOP: Expected batch directory layout differs"

if target.is_symlink():
    assert os.readlink(target) == container_source, \
        "STOP: Existing link points elsewhere"
    print("NLP LINK: ALREADY CORRECT")
else:
    assert not target.exists(), \
        "STOP: Existing batch weight directory preserved"
    target.symlink_to(container_source, target_is_directory=True)
    print("NLP LINK: CREATED")

print("NLP WEIGHTS VALIDATED:", len(files))
print("SOURCE:", source)
print("CONTAINER SOURCE:", container_source)
print("DS CODE: UNCHANGED")
print("WORKING MODEL: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
