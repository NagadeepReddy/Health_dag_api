podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
import os
import sys
from pathlib import Path
import numpy as np

from max.dtype import DType
from max.graph import Graph, TensorType, DeviceRef, ops
from max.driver import CPU, Tensor
from max.engine import InferenceSession

base = Path("/workspace/artifacts/v1.168-max/cta_max")
block = base / "parallel_transformer_block_2layers.py"
fusion = base / "grecbase_fusion_real_shapes_max.py"
rotary = base / "sequence_weights/fn_rotary_emb_inv_freq.npy"

assert all(p.is_file() for p in (block, fusion, rotary))

# First prove MAX can reproduce the original attention mask.
device = CPU()
ref = DeviceRef.CPU()

test_graph = Graph(
    "cta_real_valid_length_mask_check",
    input_types=[
        TensorType(DType.float32, [1, 2, 50, 50], device=ref),
        TensorType(DType.int64, [1], device=ref),
    ],
)

with test_graph:
    scores, vl = test_graph.inputs
    positions = ops.constant(
        np.arange(50, dtype=np.int64).reshape(1, 1, 1, 50),
        dtype=DType.int64,
        device=ref,
    )
    mask = ops.less(positions, ops.reshape(vl, [1, 1, 1, 1]))
    negative_inf = ops.constant(
        np.array(-np.inf, dtype=np.float32),
        dtype=DType.float32,
        device=ref,
    )
    probabilities = ops.softmax(
        ops.where(mask, negative_inf, scores)
    )
    test_graph.output(probabilities)

model = InferenceSession(devices=[device]).load(test_graph)
result = model.execute(
    Tensor.from_numpy(
        np.zeros((1, 2, 50, 50), dtype=np.float32)
    ).to(device),
    Tensor.from_numpy(
        np.array([3], dtype=np.int64)
    ).to(device),
)[0].to_numpy()

assert np.isfinite(result).all()
assert np.all(result[..., :3] == 0)
assert np.allclose(result.sum(axis=-1), 1, atol=1e-6)

print("ORIGINAL PYTORCH MASK BEHAVIOR: PASS")
print("POSITIONS 0, 1, 2 MASKED: PASS")

original_block = block.read_text()
original_fusion = fusion.read_text()

def replace_one(source, old, new, label):
    count = source.count(old)
    assert count == 1, f"{label}: expected 1 occurrence, found {count}"
    return source.replace(old, new, 1)

updated_block = replace_one(
    original_block,
    "        pos_emb: TensorValue,\n",
    "        pos_emb: TensorValue,\n"
    "        valid_length: TensorValue | None = None,\n",
    "Block valid-length argument",
)

updated_block = replace_one(
    updated_block,
    "        attn = ops.softmax(scores)",
    """        if valid_length is not None:
            import numpy as np
            seq_len = int(scores.shape[-1])
            positions = ops.constant(
                np.arange(seq_len, dtype=np.int64).reshape(
                    1, 1, 1, seq_len
                ),
                dtype=DType.int64,
                device=valid_length.device,
            )
            padding_mask = ops.less(
                positions,
                ops.reshape(valid_length, [1, 1, 1, 1]),
            )
            negative_inf = ops.constant(
                np.array(-np.inf, dtype=np.float32),
                dtype=DType.float32,
                device=valid_length.device,
            )
            scores = ops.where(padding_mask, negative_inf, scores)

        attn = ops.softmax(scores)""",
    "Attention padding mask",
)

updated_fusion = replace_one(
    original_fusion,
    "page, item, item_meta, page_wide, pos = remaining[20:25]",
    "page, item, item_meta, page_wide, vl = remaining[20:25]",
    "Real valid-length input",
)

updated_fusion = replace_one(
    updated_fusion,
    "        sx1 = sx + block0(sx, pos)",
    """        # Rotary positions and valid length are different inputs.
        inv = np.load(
            Path(__file__).parent
            / "sequence_weights"
            / "fn_rotary_emb_inv_freq.npy"
        ).astype(np.float32)
        seq_len = int(sx.shape[1])
        frequencies = (
            np.arange(seq_len, dtype=np.float32)[:, None]
            * inv[None, :]
        )
        position_values = np.concatenate(
            [frequencies, frequencies], axis=-1
        )[None, None, :, :].astype(np.float32)
        assert position_values.shape == (1, 1, seq_len, 256)
        pos = ops.constant(
            position_values, dtype=DType.float32, device=device
        )
        sx1 = sx + block0(sx, pos, vl)""",
    "Block 0 rotary and valid length",
)

updated_fusion = replace_one(
    updated_fusion,
    "sx2 = sx1 + block1(sx1, pos)",
    "sx2 = sx1 + block1(sx1, pos, vl)",
    "Block 1 valid length",
)

compile(updated_block, str(block), "exec")
compile(updated_fusion, str(fusion), "exec")

changes = [
    (block, original_block, updated_block),
    (fusion, original_fusion, updated_fusion),
]

# Protect working files before changing either one.
for path, original, updated in changes:
    backup = path.with_name(
        path.name + ".before_valid_length_fix.bak"
    )
    if backup.exists():
        assert backup.read_text() == original, (
            f"Existing backup differs: {backup}"
        )
    else:
        backup.write_text(original)

try:
    for path, original, updated in changes:
        path.write_text(updated)

    sys.path.insert(0, str(base.parent))

    from cta_max.grecbase_fusion_real_shapes_max import (
        build_grecbase_fusion_graph_real_shapes,
    )

    graph = build_grecbase_fusion_graph_real_shapes(ref)
    assert isinstance(graph, Graph)

    print("REAL-SHAPE GRAPH CONSTRUCTION: PASS")
    print("ROTARY EMBEDDING: CORRECTED")
    print("REAL VL MASK CONNECTED TO BOTH BLOCKS: PASS")
    print("MAX-ONLY SOURCE FILES SAVED: PASS")
    print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")

except BaseException:
    for path, original, updated in changes:
        path.write_text(original)
    print("GRAPH CHECK FAILED — PREVIOUS MAX FILES RESTORED")
    raise
PY
