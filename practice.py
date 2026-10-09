cat > artifacts/v1.168-max/cta_max/parallel_transformer_graph.py <<'PY'
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.nn import Signals

from parallel_transformer_block import ParallelTransformerBlockMAX


def build_parallel_transformer_graph(
    device_ref: DeviceRef,
    weights_registry,
):
    """Build MAX graph for CTA sequence transformer block 0."""

    block = ParallelTransformerBlockMAX(
        dtype=DType.float32,
        device=device_ref,
    )

    # Same deterministic parity input shape already saved:
    # [batch=1, sequence=4, dim=256]
    x_type = TensorType(
        DType.float32,
        shape=[1, 4, 256],
        device=device_ref,
    )

    # Rotary position embedding:
    # broadcastable to Q/K [B, H, N, 256].
    pos_type = TensorType(
        DType.float32,
        shape=[1, 1, 4, 256],
        device=device_ref,
    )

    graph = Graph(
        "cta_parallel_transformer_block_0",
        input_types=[x_type, pos_type],
    )

    with graph:
        x, pos_emb = graph.inputs
        output = block(x, pos_emb)

        graph.output(output)

    return graph
PY

echo "TRANSFORMER MAX GRAPH BUILDER CREATED"
