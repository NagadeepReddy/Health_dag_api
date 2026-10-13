cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, "/workspace/artifacts/v1.168-max")

from max.driver import CPU, Tensor
from max.dtype import DType
from max.graph import Graph, TensorType, DeviceRef
from max.engine import InferenceSession
from cta_max.grecbase_get_path_max import grecbase_get_path_max

b = Path("/workspace/artifacts/v1.168-max/cta_max")
w = b / "get_path_weights"

fusion = np.load(
    b / "real_sanity_max_2048_verified_latest.npy"
).astype(np.float32)

pt_fusion = np.load(
    b / "real_sanity_pytorch_same_input_verified.npz"
)["final"].astype(np.float32)

assert fusion.shape == pt_fusion.shape == (1, 2048)
fusion_diff = float(np.max(np.abs(fusion - pt_fusion)))
print("FUSION MAX DIFF:", fusion_diff)
assert fusion_diff < 1e-3, "STOP: Saved fusion not verified"

device = DeviceRef.CPU()
graph = Graph(
    "cta_real_fusion_to_trained_head",
    input_types=[TensorType(DType.float32, [1, 2048], device=device)]
)

with graph:
    graph.output(grecbase_get_path_max(graph.inputs[0], device))

session = InferenceSession(devices=[CPU()])
model = session.load(graph)
mx = model.execute(Tensor.from_numpy(fusion).to(CPU()))[0].to_numpy()

def weight(name):
    return torch.from_numpy(
        np.load(w / (name + ".npy")).astype(np.float32)
    )

with torch.no_grad():
    x = torch.from_numpy(pt_fusion)
    x = F.linear(x, weight("remove_tasks_dense1.weight"),
                 weight("remove_tasks_dense1.bias"))
    a = F.linear(x, weight("remove_tasks_act1.w1.weight"))
    c = F.linear(x, weight("remove_tasks_act1.w3.weight"))
    pt = F.linear(
        F.silu(a) * c,
        weight("remove_tasks_act1.w2.weight")
    ).numpy()

assert mx.shape == pt.shape == (1, 2048)
diff = np.abs(mx - pt)
passed = bool(np.allclose(mx, pt, rtol=1e-3, atol=1e-3))

print("COMBINED OUTPUT:", mx.shape)
print("COMBINED MAX DIFF:", float(diff.max()))
print("COMBINED MEAN DIFF:", float(diff.mean()))
print("COMBINED PARITY:", passed)

assert passed, "STOP: Combined parity failed"

saved = b / "real_sanity_max_get_path_verified_latest.npy"
assert not saved.exists(), "STOP: Output already exists"
np.save(saved, mx)
print("VERIFIED COMBINED OUTPUT SAVED:", saved)
PY
