cat > artifacts/v1.168-max/cta_max/context_head_wide_graph.py <<'PY'
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from cta_max.context_head_wide import ContextHeadWideMAX


def build_context_head_wide_graph(device: DeviceRef) -> Graph:
    input_types = [
        TensorType(DType.float32, shape=[1, 127], device=device),  # wide_in
        TensorType(DType.float32, shape=[127], device=device),     # BN weight
        TensorType(DType.float32, shape=[127], device=device),     # BN bias
        TensorType(DType.float32, shape=[127], device=device),     # running mean
        TensorType(DType.float32, shape=[127], device=device),     # running var
    ]

    with Graph("cta_context_head_wide", input_types=input_types) as graph:
        model = ContextHeadWideMAX(DType.float32, device)

        output = model(
            graph.inputs[0],
            graph.inputs[1],
            graph.inputs[2],
            graph.inputs[3],
            graph.inputs[4],
        )

        graph.output(output)

    return graph
PY
