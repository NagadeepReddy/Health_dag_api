podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import ast
from pathlib import Path

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
sys.path.insert(0, str(root))
sys.path.insert(0, str(base))

previous = base / "grecbase_fusion_with_nlp_max.py"
target = base / "grecbase_fusion_all8_max.py"

assert previous.exists(), "Validated six-branch graph missing"

source = previous.read_text()

def change(old, new):
    global source
    assert source.count(old) == 1, (
        "Unexpected source; no file changed: " + old[:75]
    )
    source = source.replace(old, new)

# Reuse the exact sequence classes already implemented.
seq_file = root / "parallel_transformer_block_2layers.py"
if seq_file.exists():
    block_import = (
        "from parallel_transformer_block_2layers "
        "import ParallelTransformerBlockMAX"
    )
else:
    assert (base / "parallel_transformer_block_2layers.py").exists()
    block_import = (
        "from cta_max.parallel_transformer_block_2layers "
        "import ParallelTransformerBlockMAX"
    )

change(
    "from cta_max.nlp_bert_in_graph import nlp_bert_forward",
    "from cta_max.nlp_bert_in_graph import nlp_bert_forward\n"
    "from cta_max.sequence_transformer_max import ParallelTransformerMAEPMAX\n"
    "from cta_max.sequence_postprocess_max import SequencePostprocessMAX\n"
    "from cta_max.sibling_context_max import sibling_context_forward\n"
    + block_import
)

change(
    "def build_grecbase_fusion_graph_with_nlp(device):",
    "def build_grecbase_fusion_graph_all8(device):"
)

change(
    "seq, sibling, task0, task1, ihq_ids, jet_name, jet_status, *remaining = graph.inputs",
    "task0, task1, ihq_ids, jet_name, jet_status, *remaining = graph.inputs"
)

change("assert len(remaining) == 20", "assert len(remaining) == 37")

change(
    "input_ids, attention_mask = remaining[18:]",
    """input_ids, attention_mask = remaining[18:20]
        page, item, item_meta, page_wide, pos = remaining[20:25]
        sibling_inputs = remaining[25:37]

        # Existing complete two-layer sequence transformer.
        features = ParallelTransformerMAEPMAX(
            dtype=DType.float32, device=device
        )
        block0 = ParallelTransformerBlockMAX(
            dtype=DType.float32, device=device, layer_idx=0
        )
        block1 = ParallelTransformerBlockMAX(
            dtype=DType.float32, device=device, layer_idx=1
        )
        postprocess = SequencePostprocessMAX(
            dtype=DType.float32, device=device
        )

        sx = features(page, item, item_meta, item, page_wide)
        sx1 = sx + block0(sx, pos)
        sx2 = sx1 + block1(sx1, pos)
        seq_raw = postprocess(sx2)

        # Original GRecBase sequence projection.
        seq_w_files = list(
            Path(__file__).parent.rglob("seq_dense.weight.npy")
        )
        seq_b_files = list(
            Path(__file__).parent.rglob("seq_dense.bias.npy")
        )
        assert len(seq_w_files) == len(seq_b_files) == 1

        sw = np.load(seq_w_files[0]).astype(np.float32)
        sb = np.load(seq_b_files[0]).astype(np.float32)
        assert sw.shape == (256, 256), sw.shape
        assert sb.shape == (256,), sb.shape

        seq = ops.matmul(
            seq_raw,
            ops.constant(
                sw.T, dtype=DType.float32, device=device
            )
        ) + ops.constant(
            sb, dtype=DType.float32, device=device
        )

        # Existing sibling context applied to three siblings.
        sibling_outputs = []
        for i in range(3):
            part = sibling_inputs[4*i:4*i+4]
            sibling_value = sibling_context_forward(
                part[:3], part[3], device
            )
            sibling_outputs.append(
                ops.reshape(sibling_value, [1, 1, 128])
            )

        sibling_stack = ops.concat(sibling_outputs, axis=1)
        sibling = ops.concat(
            [
                ops.mean(sibling_stack, axis=1),
                ops.max(sibling_stack, axis=1)
            ],
            axis=1
        )"""
)

# Append the verified sequence and sibling input contracts
# without disturbing the six existing branches.
tree = ast.parse(source)
graphs = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "Graph"
]
assert len(graphs) == 1, "Expected one fusion graph"

input_keyword = next(
    k for k in graphs[0].keywords
    if k.arg == "input_types"
)

extra_inputs = ast.parse("""
[
    TensorType(DType.int64, [1, 4], device=device),
    TensorType(DType.int64, [1, 4, 1], device=device),
    TensorType(DType.int64, [1, 4, 1], device=device),
    TensorType(DType.float32, [1, 1, 4, 256], device=device),
    TensorType(DType.float32, [1, 1, 4, 256], device=device),
] +
[
    t
    for _ in range(3)
    for t in (
        TensorType(DType.int64, [1], device=device),
        TensorType(DType.int64, [1], device=device),
        TensorType(DType.int64, [1], device=device),
        TensorType(DType.float32, [1, 127], device=device),
    )
]
""", mode="eval").body

# Remove the two previous synthetic sequence/sibling inputs.
# Preserve every other existing input.
old_inputs = ast.unparse(input_keyword.value)
assert "range(2)" in old_inputs

first = input_keyword.value
while isinstance(first, ast.BinOp):
    first = first.left

assert isinstance(first, ast.ListComp)
first.generators[0].iter = ast.parse(
    "range(0)", mode="eval"
).body

input_keyword.value = ast.BinOp(
    left=input_keyword.value,
    op=ast.Add(),
    right=extra_inputs
)

tree = ast.fix_missing_locations(tree)
updated = ast.unparse(tree) + "\n"
compile(updated, str(target), "exec")

if target.exists():
    assert target.read_text() == updated, (
        "Existing all-eight file differs; not overwritten"
    )
else:
    target.write_text(updated)

print("EIGHT-BRANCH MAX SOURCE: READY")
print("PYTHON SYNTAX: PASS")

from max.graph import DeviceRef
from cta_max.grecbase_fusion_all8_max import (
    build_grecbase_fusion_graph_all8
)

graph = build_grecbase_fusion_graph_all8(DeviceRef.CPU())

print("EIGHT-BRANCH GRAPH CONSTRUCTION: PASS")
print("ORIGINAL SIX-BRANCH GRAPH UNCHANGED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
