podman run --rm -i -v "$PWD:/workspace" -w /workspace --entrypoint python docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import importlib
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

from max.dtype import DType
from max.graph import Graph, TensorType, DeviceRef
from max.driver import CPU, Tensor
from max.engine import InferenceSession

root = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, str(root.parent))
gp = importlib.import_module("cta_max.grecbase_get_path_max")

checkpoint = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
input_file = root / "real_sanity_max_2048.npy"

required = [
    "remove_tasks_dense1.weight",
    "remove_tasks_dense1.bias",
    "remove_tasks_act1.w1.weight",
    "remove_tasks_act1.w2.weight",
    "remove_tasks_act1.w3.weight",
    "remove_tasks_dense2.weight",
]

state = torch.load(checkpoint, map_location="cpu", weights_only=True)
if "state_dict" in state:
    state = state["state_dict"]

missing = [k for k in required if k not in state]
if missing:
    raise RuntimeError(f"Missing checkpoint keys: {missing}")

assert input_file.is_file(), f"Missing saved input: {input_file}"
x = np.load(input_file).astype(np.float32)
assert x.shape == (1, 2048), f"Unexpected input shape: {x.shape}"

dest = Path(gp.WEIGHTS)
assert dest.resolve().is_relative_to(root.resolve()), (
    f"Unexpected MAX weight location: {dest}"
)

# Verify all existing files before writing anything.
for key in required:
    path = dest / (key + ".npy")
    expected = state[key].detach().cpu().numpy().astype(np.float32)
    if path.exists():
        actual = np.load(path)
        if not np.array_equal(actual, expected):
            raise RuntimeError(f"Existing weight differs: {path}")

dest.mkdir(parents=True, exist_ok=True)
created = []
for key in required:
    path = dest / (key + ".npy")
    if not path.exists():
        np.save(path, state[key].detach().cpu().numpy().astype(np.float32))
        created.append(key)

print("WEIGHTS READY:", len(required))
print("NEW WEIGHT FILES:", created)

def linear(v, name, bias=False):
    w = state[name + ".weight"].float()
    b = state[name + ".bias"].float() if bias else None
    return F.linear(v, w, b)

with torch.no_grad():
    t = torch.from_numpy(x)
    t = linear(t, "remove_tasks_dense1", bias=True)
    a = linear(t, "remove_tasks_act1.w1")
    b = linear(t, "remove_tasks_act1.w3")
    t = linear(F.silu(a) * b, "remove_tasks_act1.w2")
    pytorch_out = linear(t, "remove_tasks_dense2").numpy()

device = CPU()
device_ref = DeviceRef.from_device(device)

with Graph(
    "cta_get_path_isolated_parity",
    input_types=[TensorType(DType.float32, [1, 2048], device_ref)],
) as graph:
    graph.output(gp.grecbase_get_path_max(graph.inputs[0], device_ref))

session = InferenceSession(devices=[device])
model = session.load(graph)
max_out = model.execute(Tensor.from_numpy(x))[0].to_numpy()

diff = np.abs(pytorch_out.astype(np.float64) - max_out.astype(np.float64))

print("\n=== ISOLATED FINAL GET_PATH PARITY ===")
print("PYTORCH SHAPE:", pytorch_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFFERENCE:", float(diff.max()))
print("MEAN DIFFERENCE:", float(diff.mean()))
print("MATCH:", bool(np.allclose(pytorch_out, max_out, rtol=1e-3, atol=1e-3)))
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
