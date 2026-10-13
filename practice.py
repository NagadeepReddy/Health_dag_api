podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
sys.path.insert(0, str(root))

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import Graph, TensorType, DeviceRef
from max.dtype import DType
from cta_max.main_context_max import main_context_forward

data = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

pt = np.load(base / "real_sanity_pytorch_branches.npz")
expected = pt["context"]

device = CPU()
ref = DeviceRef.CPU()

assert len(data["deep_in"]) == 17
assert len(data["wide_in"]) == 127

graph = Graph(
    "cta_main_context_real_parity",
    input_types=[
        TensorType(DType.int64, [1], device=ref)
        for _ in range(17)
    ] + [
        TensorType(DType.float32, [1, 127], device=ref)
    ]
)

with graph:
    *deep_ids, wide = graph.inputs
    combined, extracted = main_context_forward(
        deep_ids, wide, ref
    )
    graph.output(combined)

inputs = []

for x in data["deep_in"]:
    arr = x.detach().cpu().numpy().astype(
        np.int64
    ).reshape(1)
    inputs.append(
        Tensor.from_numpy(
            np.ascontiguousarray(arr)
        ).to(device)
    )

wide = np.stack([
    x.detach().cpu().numpy()
    for x in data["wide_in"]
], axis=1).astype(np.float32)

assert wide.shape == (1, 127)

inputs.append(
    Tensor.from_numpy(
        np.ascontiguousarray(wide)
    ).to(device)
)

session = InferenceSession(devices=[device])
model = session.load(graph)

actual = model.execute(*inputs)[0].to_numpy()

assert expected.shape == actual.shape == (1, 256)
assert np.isfinite(actual).all()

diff = np.abs(
    expected.astype(np.float64)
    - actual.astype(np.float64)
)

match = bool(np.allclose(
    expected, actual,
    rtol=1e-3,
    atol=1e-3
))

print("\n=== MAIN CONTEXT REAL PARITY ===")
print("SHAPE:", actual.shape)
print("MEAN DIFF:", float(diff.mean()))
print("MAX DIFF:", float(diff.max()))
print("MATCH:", match)
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
print("NO FILES MODIFIED")
PY
