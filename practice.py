cat > artifacts/v1.168-max/cta_max/test_transformer_rms_max.py <<'PY'
import numpy as np

from max.driver import CPU, Tensor
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops
from max.graph.weights import WeightData
from max.graph import Shape
from max.nn import RMSNorm

BASE = "artifacts/v1.168-max/cta_max"
device = CPU()
device_ref = DeviceRef.from_device(device)

x = np.load(BASE + "/transformer_input.npy").astype(np.float32)
g = np.load(BASE + "/sequence_weights/fn_norm1_g.npy").astype(np.float32)

weights = {
    "weight": WeightData(
        g,
        name="weight",
        dtype=DType.float32,
        shape=Shape(g.shape),
    )
}

with Graph(
    "transformer_rms_test",
    input_types=[
        TensorType(DType.float32, list(x.shape), device=device_ref)
    ],
) as graph:
    inp = graph.inputs[0]
    norm = RMSNorm(256, dtype=DType.float32, eps=1e-6)
    out = norm(inp)
    graph.output(out)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

result = model.execute(Tensor.from_numpy(x))[0]
max_rms = np.asarray(result)

np.save(BASE + "/transformer_rms_max.npy", max_rms)

pt_rms = np.load(BASE + "/transformer_rms_pytorch.npy")

print("PT SHAPE :", pt_rms.shape)
print("MAX SHAPE:", max_rms.shape)
print("MAX DIFF :", np.max(np.abs(pt_rms - max_rms)))
print("MATCH    :", np.allclose(pt_rms, max_rms, rtol=1e-4, atol=1e-5))
PY

echo "MAX RMS TEST CREATED"
