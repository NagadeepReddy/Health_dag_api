cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import shutil

src = Path("artifacts/v1.168-max/cta_max/grecbase_integration_weights")
dst = Path("/application1/cta_max_true_batch_dev_20261028/cta_max/grecbase_integration_weights")
stage = dst.with_name("grecbase_integration_weights_copy_pending")

expected_link = "/workspace/artifacts/v1.168-max/cta_max/grecbase_integration_weights"
weight = "att_pooling.rotary_emb.inv_freq.npy"

assert src.is_dir(), "STOP: Original weights directory missing"
assert (src / weight).is_file(), "STOP: Original rotary weight missing"
assert dst.is_symlink(), "STOP: Target is not the expected symlink"
assert str(dst.readlink()) == expected_link, "STOP: Target link differs"
assert not stage.exists(), "STOP: Staging directory already exists"

shutil.copytree(src, stage)

originals = sorted(p.relative_to(src) for p in src.rglob("*.npy"))
copies = sorted(p.relative_to(stage) for p in stage.rglob("*.npy"))

assert originals and originals == copies, "STOP: Weight file mismatch"
assert (stage / weight).read_bytes() == (src / weight).read_bytes(), \
    "STOP: Rotary weight differs"

dst.unlink()
stage.rename(dst)

print("ROTARY WEIGHTS: COPIED")
print("WEIGHT FILES:", len(copies))
print("ROTARY WEIGHT: VERIFIED")
print("BATCH DIRECTORY: READY")
print("ORIGINAL WEIGHTS: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
