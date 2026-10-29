cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import hashlib

repo = Path.cwd()
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/run_batch2_live_max_inference.py")
dst = dev / "run_distinct_batch2_live_max_inference.py"

assert src.is_file(), f"STOP: Successful runner missing: {src}"

code = src.read_text()
old = "arrays = pack_two_requests(arrays, arrays)"
assert code.count(old) == 1, "STOP: Original batch packing differs"

new = """\
import os
import torch
import numpy as np

second_path = os.environ.get("CTA_SECOND_MODEL_INPUT")
assert second_path, "STOP: Set CTA_SECOND_MODEL_INPUT to a second real saved model input"
assert os.path.isfile(second_path), f"STOP: Missing second input: {second_path}"

second_model_in = torch.load(
    second_path, map_location="cpu", weights_only=False
)
labels2, arrays2 = build_real_inputs(model_in=second_model_in)

assert labels == labels2, "STOP: Model input ordering differs"
assert len(arrays) == len(arrays2) == 72, "STOP: Expected 72 inputs"

for a, b in zip(arrays, arrays2):
    assert np.asarray(a).shape == np.asarray(b).shape, \
        "STOP: Incompatible model input shapes"

differences = sum(
    not np.array_equal(np.asarray(a), np.asarray(b))
    for a, b in zip(arrays, arrays2)
)
assert differences > 0, "STOP: Both real inputs are identical"

print("DISTINCT REAL INPUT TENSORS:", differences, flush=True)
arrays = pack_two_requests(arrays, arrays2)"""

updated = code.replace(
    old,
    "\n".join("    " + line if line else "" for line in new.splitlines())
)
ast.parse(updated)
assert not dst.exists() or dst.read_text() == updated, \
    "STOP: Existing development runner differs"

dev.mkdir(parents=True, exist_ok=True)
if not dst.exists():
    dst.write_text(updated)

print("DISTINCT-INPUT RUNNER: READY")
print("FILE:", dst)

print("\n=== AVAILABLE SAVED REAL MODEL INPUTS ===")
roots = [
    repo / "artifacts/v1.168-max",
    Path("/application1/cta_max_true_batch_dev_20261028"),
    dev,
]
seen = set()
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*model_in*.pt"):
        if not p.is_file():
            continue
        digest = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        if str(p) not in seen:
            print(digest.hexdigest()[:16], p)
            seen.add(str(p))

print("\nORIGINAL SUCCESSFUL RUNNER: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("REAL DISTINCT-INPUT EXECUTION: NOT YET PERFORMED")
print("MAX STARTUP: NOT PERFORMED")
PY
