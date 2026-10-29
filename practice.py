cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import re
import textwrap
import hashlib

src = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/run_batch2_live_max_inference.py")
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
dst = dev / "run_distinct_batch2_live_max_inference.py"

assert src.is_file(), f"STOP: Missing successful runner: {src}"
source = src.read_text()

pattern = r"(?m)^([ \t]*)arrays = pack_two_requests\(arrays, arrays\)[ \t]*$"
matches = list(re.finditer(pattern, source))
assert len(matches) == 1, f"STOP: Expected one batch packing call, found {len(matches)}"

block = textwrap.dedent("""
import os
import torch
import numpy as np

second_path = os.environ.get("CTA_SECOND_MODEL_INPUT")
if not second_path:
    raise RuntimeError("Set CTA_SECOND_MODEL_INPUT to a second genuine saved model input")

if not os.path.isfile(second_path):
    raise FileNotFoundError(second_path)

second_model_in = torch.load(
    second_path, map_location="cpu", weights_only=True
)
labels2, arrays2 = build_real_inputs(model_in=second_model_in)

assert labels == labels2, "Model input order differs"
assert len(arrays) == len(arrays2) == 72, "Expected 72 model inputs"

different = 0
for first, second in zip(arrays, arrays2):
    a = np.asarray(first)
    b = np.asarray(second)
    assert a.shape == b.shape, "Incompatible input shapes"
    if not np.array_equal(a, b):
        different += 1

assert different > 0, "STOP: Inputs are identical"
print("DISTINCT REAL INPUT TENSORS:", different, flush=True)

arrays = pack_two_requests(arrays, arrays2)
""").strip()

m = matches[0]
indent = m.group(1)
replacement = textwrap.indent(block, indent)

updated = source[:m.start()] + replacement + source[m.end():]

# The successful runner uses its own directory to resolve assets.
old_base = "BASE = Path(__file__).resolve().parent"
assert updated.count(old_base) == 1, "STOP: Runner BASE differs"
updated = updated.replace(
    old_base,
    f"BASE = Path({str(src.parent)!r})"
)

ast.parse(updated)
compile(updated, str(dst), "exec")

dev.mkdir(parents=True, exist_ok=True)

if dst.exists():
    assert dst.read_text() == updated, "STOP: Existing development runner differs"
    print("RUNNER: EXISTING VERSION VERIFIED")
else:
    dst.write_text(updated)
    print("RUNNER: CREATED")

print("PYTHON SYNTAX: PASS")
print("SUCCESSFUL ORIGINAL RUNNER: UNCHANGED")

print("\n=== GENUINE SAVED MODEL INPUT CANDIDATES ===")

roots = [
    Path("artifacts/v1.168-max"),
    Path("/application1/cta_max_true_batch_dev_20261028"),
    dev,
]

seen_hashes = set()
for root in roots:
    if not root.is_dir():
        continue
    for p in sorted(root.rglob("*model_in*.pt")):
        if not p.is_file():
            continue
        digest = hashlib.sha256()
        with p.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        h = digest.hexdigest()
        if h not in seen_hashes:
            print(h[:16], p.resolve())
            seen_hashes.add(h)

print("UNIQUE SAVED FILES:", len(seen_hashes))
print("DISTINCT-INPUT EXECUTION: NOT YET PERFORMED")
print("NATIVE AUTOMATIC BATCHING: PENDING")
print("GPU VALIDATION: PENDING")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
