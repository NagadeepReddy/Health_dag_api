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
sequence_file = base / "parallel_transformer_graph_full_sequence.py"

assert previous.exists()
assert sequence_file.exists()

source = previous.read_text()

def change(old, new):
    global source
    assert source.count(old) == 1, (
        "Unexpected source; previous graph preserved: " + old[:65]
    )
    source = source.replace(old, new)

# Reuse exact imports from the existing sequence implementation.
seq_tree = ast.parse(sequence_file.read_text())
needed = {
    "ParallelTransformerMAEPMAX",
    "ParallelTransformerBlockMAX",
    "SequencePostprocessMAX",
}

imports = []
for node in seq_tree.body:
    if isinstance(node, ast.ImportFrom):
        if any(alias.name in needed for alias in node.names):
            imports.append(ast.unparse(node))

assert len(imports) == 3, imports

change(
    "from cta_max.nlp_bert_in_graph import nlp_bert_forward",
    "from cta_max.nlp_bert_in_graph import nlp_bert_forward\n"
    "from cta_max.sibling_context_max import sibling_context_forward\n"
    + "\n".join(imports)
)

change(
    "def build_grecbase_fusion_graph_with_nlp(device):",
    "def build_grecbase_fusion_graph_all8(device):"
)

change(
    "seq, sibling, task0, task1, ihq_ids, jet_name, jet_status, *remaining = graph.inputs",
    "task0, task1, ihq_ids, jet_name, jet_status, *remaining = graph.inputs"
)

change(
    "assert len(remaining) == 20",
    "assert len(remaining) == 37"
)

change(
    "input_ids, attention_mask = remaining[18:]",
    """input_ids, attention_mask = remaining[18:20]
        page, item, item_meta, page_wide, pos = remaining[20:25]
        sibling_inputs = remaining[25:37]

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

        seq_w = np.load(
            WDIR / "seq_dense.weight.npy"
        ).astype(np.float32)
        seq_b = np.load(
            WDIR / "seq_dense.bias.npy"
        ).astype(np.float32)

        assert seq_w.shape == (256, 256)
        assert seq_b.shape == (256,)

        seq = ops.matmul(
            seq_raw,
            ops.constant(
                seq_w.T, dtype=DType.float32, device=device
            )
        ) + ops.constant(
            seq_b, dtype=DType.float32, device=device
        )

        sibling_outputs = []
        for i in range(3):
            part = sibling_inputs[i*4:(i+1)*4]
            value = sibling_context_forward(
                part[:3], part[3], device
            )
            sibling_outputs.append(
                ops.reshape(value, [1, 1, 128])
            )

        sibling_stack = ops.concat(
            sibling_outputs, axis=1
        )

        sibling = ops.concat(
            [
                ops.mean(sibling_stack, axis=1),
                ops.max(sibling_stack, axis=1)
            ],
            axis=1
        )"""
)

# Add the 5 sequence and 12 sibling inputs.
# Parenthesized expression fixes the previous syntax error.
extra = ast.parse("""
(
    [
        TensorType(DType.int64, [1, 4], device=device),
        TensorType(DType.int64, [1, 4, 1], device=device),
        TensorType(DType.int64, [1, 4, 1], device=device),
        TensorType(DType.float32, [1, 1, 4, 256], device=device),
        TensorType(DType.float32, [1, 1, 4, 256], device=device),
    ]
    +
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
)
""", mode="eval").body

tree = ast.parse(source)

graphs = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "Graph"
]
assert len(graphs) == 1

kw = next(
    k for k in graphs[0].keywords
    if k.arg == "input_types"
)

# Remove the two synthetic Sequence/Sibling inputs.
left = kw.value
while isinstance(left, ast.BinOp):
    left = left.left

assert isinstance(left, ast.ListComp)
assert ast.unparse(left.generators[0].iter) == "range(2)"

left.generators[0].iter = ast.parse(
    "range(0)", mode="eval"
).body

kw.value = ast.BinOp(
    left=kw.value,
    op=ast.Add(),
    right=extra
)

updated = ast.unparse(ast.fix_missing_locations(tree)) + "\n"
compile(updated, str(target), "exec")

if target.exists():
    assert target.read_text() == updated, (
        "Existing file differs; not overwritten"
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
print("PREVIOUS SIX-BRANCH GRAPH UNCHANGED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
