podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
import sys
from pathlib import Path

from max.dtype import DType
from max.graph import Graph, DeviceRef
from max.driver import CPU
from max.engine import InferenceSession

base = Path("/workspace/artifacts/v1.168-max/cta_max")
block = base / "parallel_transformer_block_2layers.py"
fusion = base / "grecbase_fusion_real_shapes_max.py"

assert block.is_file() and fusion.is_file()

old_block = block.read_text()
old_fusion = fusion.read_text()

def replace_once(source, before, after, label):
    count = source.count(before)
    assert count == 1, f"{label}: found {count}, expected 1"
    return source.replace(before, after, 1)

# 1. Add a separate optional valid-length argument.
new_block = replace_once(
    old_block,
    "        pos_emb: TensorValue,\n",
    "        pos_emb: TensorValue,\n"
    "        valid_length: TensorValue | None = None,\n",
    "block argument"
)

# 2. Reproduce the verified PyTorch masking behavior.
new_block = replace_once(
    new_block,
    "        attn = ops.softmax(scores)",
    """        if valid_length is not None:
            import numpy as np
            n = int(scores.shape[-1])
            positions = ops.constant(
                np.arange(n, dtype=np.int64).reshape(1, 1, 1, n),
                dtype=DType.int64,
                device=DeviceRef.CPU(),
            )
            mask = ops.greater(
                ops.reshape(valid_length, [1, 1, 1, 1]),
                positions,
            )
            negative_inf = ops.constant(
                np.array(-np.inf, dtype=np.float32),
                dtype=DType.float32,
                device=DeviceRef.CPU(),
            )
            scores = ops.where(mask, negative_inf, scores)
        attn = ops.softmax(scores)""",
    "attention mask"
)

# 3. Keep the existing rotary input.
#    Add valid length as a NEW graph input instead.
new_fusion = replace_once(
    old_fusion,
    "assert len(remaining) == 65",
    "assert len(remaining) == 66",
    "fusion input count"
)

new_fusion = replace_once(
    new_fusion,
    "sibling_inputs = remaining[25:65]",
    "sibling_inputs = remaining[25:65]\n"
    "        vl = remaining[65]",
    "valid-length binding"
)

new_fusion = replace_once(
    new_fusion,
    "sx1 = sx + block0(sx, pos)",
    "sx1 = sx + block0(sx, pos, vl)",
    "block 0"
)

new_fusion = replace_once(
    new_fusion,
    "sx2 = sx1 + block1(sx1, pos)",
    "sx2 = sx1 + block1(sx1, pos, vl)",
    "block 1"
)

# 4. Safely extend the existing graph input_types expression.
#    Preserve the other 70 input positions exactly as before.
tree = ast.parse(new_fusion)

calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "Graph"
]
assert len(calls) == 1, "Unexpected Graph construction"

keywords = [
    kw for kw in calls[0].keywords
    if kw.arg == "input_types"
]
assert len(keywords) == 1

value = keywords[0].value
lines = new_fusion.splitlines(keepends=True)

line_prefix = lines[value.end_lineno - 1].encode("utf-8")[
    :value.end_col_offset
].decode("utf-8")

offset = (
    sum(len(line) for line in lines[:value.end_lineno - 1])
    + len(line_prefix)
)

addition = " + [TensorType(DType.int64, [1], device=device)]"

new_fusion = (
    new_fusion[:offset]
    + addition
    + new_fusion[offset:]
)

# 5. Validate both proposed edits before touching files.
compile(new_block, str(block), "exec")
compile(new_fusion, str(fusion), "exec")

# Ensure the rotary input was not replaced.
assert (
    "page, item, item_meta, page_wide, pos = remaining[20:25]"
    in new_fusion
)

print("ROTARY POSITION INPUT: PRESERVED")
print("REAL VALID-LENGTH INPUT: ADDED")
print("BOTH TRANSFORMER BLOCKS: MASK CONNECTED")
print("SOURCE SYNTAX: PASS")

changes = [
    (block, old_block, new_block),
    (fusion, old_fusion, new_fusion),
]

# 6. Save backups without overwriting any existing backup.
for path, old, new in changes:
    backup = path.with_name(
        path.name + ".before_separate_vl_fix.bak"
    )
    if backup.exists():
        assert backup.read_text() == old, (
            f"Backup differs; stopping: {backup}"
        )
    else:
        backup.write_text(old)

try:
    for path, old, new in changes:
        path.write_text(new)

    sys.path.insert(0, str(base.parent))

    from cta_max.grecbase_fusion_real_shapes_max import (
        build_grecbase_fusion_graph_real_shapes
    )

    device = CPU()
    graph = build_grecbase_fusion_graph_real_shapes(
        DeviceRef.CPU()
    )

    assert isinstance(graph, Graph)
    assert len(graph.inputs) == 71, (
        f"Expected 71 inputs; got {len(graph.inputs)}"
    )

    session = InferenceSession(devices=[device])
    compiled = session.load(graph)

    print("\nREAL-SHAPE GRAPH CONSTRUCTION: PASS")
    print("REAL-SHAPE GRAPH COMPILATION: PASS")
    print("INPUT COUNT: 71")
    print("ROTARY: EXISTING INPUT PRESERVED")
    print("VALID LENGTH: SEPARATE INPUT")
    print("PADDING MASK: BOTH BLOCKS")
    print("MAX-ONLY CORRECTION: SAVED")
    print("ORIGINAL PYTORCH AND DS CODE: UNCHANGED")

except BaseException:
    for path, old, new in changes:
        path.write_text(old)
    print("\nVERIFICATION FAILED")
    print("PREVIOUS MAX FILES RESTORED")
    raise
PY
