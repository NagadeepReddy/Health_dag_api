cat > artifacts/v1.168-max/cta_max/test_transformer_fused_max.py <<'PY'
import numpy as np

from max.driver import CPU, Tensor
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, Shape
from max.graph.weights import WeightData
from max.nn import Linear

BASE = "artifacts/v1.168-max/cta_max"

device = CPU()
device_ref = DeviceRef.from_device(device)

x = np.load(BASE + "/transformer_rms_pytorch.npy").astype(np.float32)
w = np.load(
    BASE + "/sequence_weights/fn_fused_attn_ff_proj_weight.npy"
).astype(np.float32)

name = "sequence_transformer.ptransformer.0.fused_attn_ff_proj"

weights = {
    name + ".weight": WeightData(
        w,
        name=name + ".weight",
        dtype=DType.float32,
        shape=Shape(w.shape),
    )
}

with Graph(
    "transformer_fused_test",
    input_types=[
        TensorType(DType.float32, list(x.shape), device=device_ref)
    ],
) as graph:
    inp = graph.inputs[0]

    linear = Linear(
        256,
        3072,
        DType.float32,
        device_ref,
        has_bias=False,
        name=name,
    )

    out = linear(inp)
    graph.output(out)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

result = model.execute(Tensor.from_numpy(x))[0]

if hasattr(result, "to_numpy"):
    max_out = result.to_numpy()
elif hasattr(result, "numpy"):
    max_out = result.numpy()
else:
    max_out = np.asarray(result)

pt_out = np.load(BASE + "/transformer_fused_pytorch.npy")

print("PT SHAPE :", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF :", np.max(np.abs(pt_out - max_out)))
print("MATCH    :", np.allclose(pt_out, max_out, rtol=1e-4, atol=1e-5))
PY

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_fused_max.py && echo "FUSED MAX TEST CREATED - SYNTAX CLEAN"
