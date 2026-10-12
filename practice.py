python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
dst = base / "parallel_transformer_graph_full_sequence.py"

assert not dst.exists(), "STOP: graph already exists"

for name in (
    "sequence_transformer_max.py",
    "parallel_transformer_block_2layers.py",
    "sequence_postprocess_max.py",
):
    assert (base / name).is_file(), f"STOP: missing {name}"

code = '''
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType

from parallel_transformer_block_2layers import ParallelTransformerBlockMAX
from cta_max.sequence_transformer_max import ParallelTransformerMAEPMAX
from cta_max.sequence_postprocess_max import SequencePostprocessMAX


def build_parallel_transformer_graph(device_ref, weights_registry):
    features = ParallelTransformerMAEPMAX(
        dtype=DType.float32, device=device_ref
    )
    block0 = ParallelTransformerBlockMAX(
        dtype=DType.float32, device=device_ref, layer_idx=0
    )
    block1 = ParallelTransformerBlockMAX(
        dtype=DType.float32, device=device_ref, layer_idx=1
    )
    postprocess = SequencePostprocessMAX(
        dtype=DType.float32, device=device_ref
    )

    int_type = TensorType(
        DType.int64, shape=[1, 4], device=device_ref
    )
    wide_type = TensorType(
        DType.float32, shape=[1, 4, 1], device=device_ref
    )
    pos_type = TensorType(
        DType.float32, shape=[1, 1, 4, 256], device=device_ref
    )

    graph = Graph(
        "cta_full_sequence_real_features_v1",
        input_types=[
            int_type, int_type, int_type,
            wide_type, pos_type,
        ],
    )

    with graph:
        page, item, item_meta, page_wide, pos = graph.inputs

        x = features(
            page, item, item_meta, item, page_wide
        )
        x1 = x + block0(x, pos)
        x2 = x1 + block1(x1, pos)

        graph.output(postprocess(x2))

    return graph
'''

ast.parse(code)
dst.write_text(code)

print("FULL SEQUENCE GRAPH CREATED — SYNTAX OK")
print("REAL EMBEDDINGS + 2 TRANSFORMER BLOCKS + POSTPROCESS")
print("PREVIOUSLY VERIFIED FILES UNCHANGED")
PY
