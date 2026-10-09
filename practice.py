cat > artifacts/v1.168-max/cta_max/run_context_head_wide.py <<'PY'
from pathlib import Path
import numpy as np

from max.driver import CPU, Tensor
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, WeightData
from max.graph.weights import Shape

from cta_max.context_head_wide_graph import build_context_head_wide_graph


device = CPU()
device_ref = DeviceRef.from_device(device)
graph = build_context_head_wide_graph(device_ref)

weight_dir = Path("artifacts/v1.168-max/cta_max/context_head_weights")

weights = {}

for name in [
    "wide_dense.weight",
    "wide_dense.bias",
    "wide_swiglu.w1.weight",
    "wide_swiglu.w2.weight",
    "wide_swiglu.w3.weight",
]:
    arr = np.load(weight_dir / f"{name}.npy")
    registry_name = f"context_head.{name}"

    weights[registry_name] = WeightData(
        arr,
        name=registry_name,
        dtype=DType.float32,
        shape=Shape(arr.shape),
    )

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

# Deterministic input for MAX/PyTorch parity.
wide_in = np.zeros((1, 127), dtype=np.float32)

inputs = [
    Tensor.from_numpy(wide_in),
    Tensor.from_numpy(np.load(weight_dir / "num_batch_norm.weight.npy").astype(np.float32)),
    Tensor.from_numpy(np.load(weight_dir / "num_batch_norm.bias.npy").astype(np.float32)),
    Tensor.from_numpy(np.load(weight_dir / "num_batch_norm.running_mean.npy").astype(np.float32)),
    Tensor.from_numpy(np.load(weight_dir / "num_batch_norm.running_var.npy").astype(np.float32)),
]

outputs = model.execute(*inputs)

print("CONTEXTHEAD WIDE MAX REAL-WEIGHT EXECUTION SUCCESS")
print("OUTPUT:", outputs)

np.save(
    "artifacts/v1.168-max/cta_max/context_head_wide_max_output.npy",
    outputs[0].to_numpy(),
)

print("MAX WIDE OUTPUT SAVED")
PY
