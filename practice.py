podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast, sys
from pathlib import Path
import numpy as np

from max.dtype import DType
from max.graph import Graph, TensorType, DeviceRef, ops
from max.driver import CPU, Tensor
from max.engine import InferenceSession

base = Path("artifacts/v1.168-max/cta_max")
block = base / "parallel_transformer_block_2layers.py"
fusion = base / "grecbase_fusion_real_shapes_max.py"
inv_file = base / "sequence_weights/fn_rotary_emb_inv_freq.npy"

assert all(p.is_file() for p in (block, fusion, inv_file))

# Verify the supported MAX operation BEFORE changing source.
device = CPU()
ref = DeviceRef.CPU()

g = Graph("cta_mask_api_check", input_types=[
    TensorType(DType.float32, [1, 2, 50, 50], device=ref),
    TensorType(DType.int64, [1], device=ref)
])

with g:
    scores, vl = g.inputs
    positions = ops.constant(
        np.arange(50, dtype=np.int64).reshape(1, 1, 1, 50),
        dtype=DType.int64, device=ref
    )
    mask = ops.greater(
        ops.reshape(vl, [1, 1, 1, 1]), positions
    )
    neg_inf = ops.constant(
        np.array(-np.inf, dtype=np.float32),
        dtype=DType.float32, device=ref
    )
    probs = ops.softmax(ops.where(mask, neg_inf, scores))
    g.output(probs)

m = InferenceSession(devices=[device]).load(g)
out = m.execute(
    Tensor.from_numpy(
        np.zeros((1, 2, 50, 50), np.float32)
    ).to(device),
    Tensor.from_numpy(
        np.array([3], np.int64)
    ).to(device)
)[0].to_numpy()

assert np.isfinite(out).all()
assert np.all(out[..., :3] == 0)
assert np.allclose(out.sum(axis=-1), 1, atol=1e-6)
print("MAX MASK COMPILE AND EXECUTION: PASS")

def replace_once(src, old, new):
    count = src.count(old)
    assert count == 1, (old, "count:", count)
    return src.replace(old, new, 1)

old_block = block.read_text()
old_fusion = fusion.read_text()

new_block = replace_once(
    old_block,
    "        pos_emb: TensorValue,\n",
    "        pos_emb: TensorValue,\n"
    "        valid_length: TensorValue | None = None,\n"
)

new_block = replace_once(
    new_block,
    "        attn = ops.softmax(scores)",
    """        if valid_length is not None:
            import numpy as np
            n = int(scores.shape[-1])
            positions = ops.constant(
                np.arange(n, dtype=np.int64).reshape(1, 1, 1, n),
                dtype=DType.int64,
                device=valid_length.device
            )
            mask = ops.greater(
                ops.reshape(valid_length, [1, 1, 1, 1]),
                positions
            )
            neg_inf = ops.constant(
                np.array(-np.inf, dtype=np.float32),
                dtype=DType.float32,
                device=valid_length.device
            )
            scores = ops.where(mask, neg_inf, scores)
        attn = ops.softmax(scores)"""
)

new_fusion = replace_once(
    old_fusion,
    "page, item, item_meta, page_wide, pos = remaining[20:25]",
    "page, item, item_meta, page_wide, vl = remaining[20:25]"
)

new_fusion = replace_once(
    new_fusion,
    "sx1 = sx + block0(sx, pos)",
    """inv = np.load(
            Path(__file__).parent
            / "sequence_weights/fn_rotary_emb_inv_freq.npy"
        ).astype(np.float32)
        n = int(sx.shape[1])
        freq = np.arange(n, dtype=np.float32)[:, None] * inv[None, :]
        positions = np.concatenate([freq, freq], axis=-1)
        positions = positions[None, None, :, :]
        assert positions.shape == (1, 1, n, 256)
        pos = ops.constant(
            positions, dtype=DType.float32, device=device
        )
        sx1 = sx + block0(sx, pos, vl)"""
)

new_fusion = replace_once(
    new_fusion,
    "sx2 = sx1 + block1(sx1, pos)",
    "sx2 = sx1 + block1(sx1, pos, vl)"
)

compile(new_block, str(block), "exec")
compile(new_fusion, str(fusion), "exec")

changes = [
    (block, old_block, new_block),
    (fusion, old_fusion, new_fusion)
]

for path, old, new in changes:
    backup = path.with_name(path.name + ".before_vl_mask_fix.bak")
    if backup.exists():
        assert backup.read_text() == old, (
            "Existing backup differs:", backup
        )
    else:
        backup.write_text(old)

try:
    for path, old, new in changes:
        path.write_text(new)

    sys.path.insert(0, str(base.parent.resolve()))
    from cta_max.grecbase_fusion_real_shapes_max import (
        build_grecbase_fusion_graph_real_shapes
    )

    graph = build_grecbase_fusion_graph_real_shapes(ref)
    assert isinstance(graph, Graph)

    print("REAL CTA GRAPH CONSTRUCTION: PASS")
    print("REAL VALID-LENGTH MASK: CONNECTED TO BOTH BLOCKS")
    print("ROTARY POSITION INPUT: SEPARATED FROM VALID LENGTH")
    print("MAX CHANGES SAVED; BACKUPS PRESERVED")
    print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")

except BaseException:
    for path, old, new in changes:
        path.write_text(old)
    print("FAILED — PREVIOUS MAX FILES RESTORED")
    raise
PY
