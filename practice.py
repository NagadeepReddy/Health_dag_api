cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("/application1/cta_max_true_batch_dev_20261028")
target = base / "maxserve_cta_extension/cta_batch2_contract.py"

assert base.is_dir(), "STOP: Batch workspace missing"
assert not target.exists(), "STOP: Batch adapter already exists"
assert shutil.disk_usage("/application1").free > 1024**3, \
    "STOP: Insufficient disk space"

source = '''
"""Batch-two tensor contract for CTA MAX development.

Integration-only code. Does not change the original DS pipeline.
"""

EXPECTED_INPUTS = 72
EXPECTED_FEATURES = 2048


def pack_two_requests(first, second):
    import numpy as np

    if len(first) != EXPECTED_INPUTS or len(second) != EXPECTED_INPUTS:
        raise ValueError("CTA MAX requires 72 inputs per request")

    packed = []

    for index, (a, b) in enumerate(zip(first, second)):
        a = np.asarray(a)
        b = np.asarray(b)

        if a.ndim < 1 or a.shape[0] != 1:
            raise ValueError(f"Input {index}: first batch dimension must be 1")

        if a.shape != b.shape:
            raise ValueError(f"Input {index}: shapes differ")

        if a.dtype != b.dtype:
            raise ValueError(f"Input {index}: dtypes differ")

        result = np.concatenate((a, b), axis=0)

        if result.shape != (2, *a.shape[1:]):
            raise AssertionError(f"Input {index}: unexpected batch shape")

        packed.append(np.ascontiguousarray(result))

    return packed


def split_two_outputs(output):
    import numpy as np

    output = np.asarray(output)

    if output.shape != (2, EXPECTED_FEATURES):
        raise ValueError(
            f"Expected MAX output (2, 2048), got {output.shape}"
        )

    if not np.isfinite(output).all():
        raise ValueError("MAX output contains non-finite values")

    return output[0:1].copy(), output[1:2].copy()
'''

ast.parse(source)
target.write_text(source)
ast.parse(target.read_text())

print("BATCH-2 INPUT/OUTPUT ADAPTER: CREATED")
print("INPUT CONTRACT: 2 x 72")
print("EXPECTED MAX OUTPUT: (2, 2048)")
print("SYNTAX: PASS")
print("LOCATION:", target)
print("BATCH-2 GRAPH: NOT YET IMPLEMENTED")
print("WORKING HTTP 200: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MODEL STARTUP: NOT PERFORMED")
PY
