python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
out = dev / "cta_batch2_input_pack.py"

required = [
    "grecbase_fusion_full_head_72_max.py",
    "run_real_sanity_input_adapter.py",
    "run_live_max_inference.py",
    "live_cta_pipeline_bridge.py",
]

assert dev.is_dir(), "STOP: Batch-2 development directory missing"
assert all((dev / name).is_file() for name in required), \
    "STOP: Required staged MAX source missing"
assert not out.exists(), "STOP: Input packer already exists"

code = '''
"""Batch-2 input/output preparation for isolated CTA MAX development.

Does not modify the original CTA DS pipeline or production MAX serving.
"""

def pack_two_real_inputs(first, second):
    import numpy as np

    labels_a, arrays_a = first
    labels_b, arrays_b = second

    if list(labels_a) != list(labels_b):
        raise ValueError("Input names/order differ")

    if len(arrays_a) != len(arrays_b) or len(arrays_a) != len(labels_a):
        raise ValueError("Input counts differ")

    packed = []

    for name, left, right in zip(labels_a, arrays_a, arrays_b):
        a = np.asarray(left)
        b = np.asarray(right)

        if a.ndim == 0 or b.ndim == 0:
            raise ValueError(f"{name}: scalar input cannot be stacked")

        if a.shape[0] != 1 or b.shape[0] != 1:
            raise ValueError(f"{name}: expected singleton leading axis")

        if a.shape[1:] != b.shape[1:]:
            raise ValueError(f"{name}: incompatible trailing shapes")

        if a.dtype != b.dtype:
            raise ValueError(f"{name}: input dtype mismatch")

        combined = np.concatenate((a, b), axis=0)

        if combined.shape[0] != 2:
            raise AssertionError(f"{name}: invalid batch dimension")

        packed.append(combined)

    return list(labels_a), packed


def split_two_max_outputs(output):
    import numpy as np

    result = np.asarray(output)

    if result.shape != (2, 2048):
        raise ValueError(
            f"Expected batched MAX output (2,2048), got {result.shape}"
        )

    return result[0:1], result[1:2]
'''

ast.parse(code)
compile(code, str(out), "exec")

# Validate both helper contracts without importing MAX or NumPy.
tree = ast.parse(code)
names = {
    node.name for node in tree.body
    if isinstance(node, ast.FunctionDef)
}
assert names == {
    "pack_two_real_inputs",
    "split_two_max_outputs"
}

out.write_text(code)
assert out.read_text() == code

print("BATCH-2 INPUT PACKER: CREATED")
print("INPUT BATCH DIMENSION: 2")
print("EXPECTED OUTPUT: (2, 2048)")
print("INPUT ORDER AND DTYPES: GUARDED")
print("PYTHON SYNTAX: PASS")
print("RUNTIME BATCHING TEST: NOT YET PERFORMED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
print("FILE:", out)
PY
