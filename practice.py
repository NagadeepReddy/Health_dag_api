podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import ast
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops

base = Path("artifacts/v1.168-max/cta_max")
checkpoint = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
dest = base / "get_path_weights"
module_file = base / "grecbase_get_path_max.py"

assert checkpoint.is_file(), "STOP: checkpoint missing"
assert not module_file.exists(), "STOP: MAX get_path already exists"
assert hasattr(ops, "sigmoid"), "STOP: MAX sigmoid unavailable"

expected = {
    "remove_tasks_dense1.weight": (2048, 2048),
    "remove_tasks_dense1.bias": (2048,),
    "remove_tasks_act1.w1.weight": (1366, 2048),
    "remove_tasks_act1.w2.weight": (2048, 1366),
    "remove_tasks_act1.w3.weight": (1366, 2048),
}

state = torch.load(
    checkpoint, map_location="cpu",
    weights_only=True, mmap=True
)

if "state_dict" in state:
    state = state["state_dict"]
elif "model_state_dict" in state:
    state = state["model_state_dict"]

arrays = {}
for name, shape in expected.items():
    assert name in state, f"STOP: missing {name}"
    arr = state[name].detach().cpu().numpy().astype(np.float32)
    assert arr.shape == shape, f"STOP: shape mismatch: {name}"
    assert np.isfinite(arr).all(), f"STOP: nonfinite weight: {name}"
    arrays[name] = arr

code = '''
from pathlib import Path
import numpy as np
from max.dtype import DType
from max.graph import ops

WEIGHTS = Path(__file__).parent / "get_path_weights"

def grecbase_get_path_max(x, device):
    def weight(name):
        arr = np.load(WEIGHTS / (name + ".npy")).astype(np.float32)
        return ops.constant(
            arr, dtype=DType.float32, device=device
        )

    def linear(v, prefix, bias=False):
        result = ops.matmul(
            v, ops.permute(weight(prefix + ".weight"), [1, 0])
        )
        if bias:
            result = result + weight(prefix + ".bias")
        return result

    x = linear(x, "remove_tasks_dense1", bias=True)

    a = linear(x, "remove_tasks_act1.w1")
    b = linear(x, "remove_tasks_act1.w3")

    activated = a * ops.sigmoid(a)
    return linear(activated * b, "remove_tasks_act1.w2")
'''

ast.parse(code)

# Check existing weights before writing anything.
for name, arr in arrays.items():
    path = dest / (name + ".npy")
    if path.exists():
        assert np.array_equal(np.load(path), arr), \
            f"STOP: existing weight differs: {name}"

dest.mkdir(parents=True, exist_ok=True)

for name, arr in arrays.items():
    path = dest / (name + ".npy")
    if not path.exists():
        np.save(path, arr)

module_file.write_text(code)
print("GET_PATH MAX COMPONENT CREATED")

sys.path.insert(0, str(base))
from grecbase_get_path_max import grecbase_get_path_max

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = Graph(
    "cta_grecbase_get_path",
    input_types=[
        TensorType(DType.float32, [1, 2048], device=device)
    ],
)

with graph:
    result = grecbase_get_path_max(graph.inputs[0], device)
    graph.output(result)

session = InferenceSession(devices=[cpu])
model = session.load(graph)

x = (
    np.random.default_rng(7)
    .standard_normal((1, 2048))
    .astype(np.float32) * 0.01
)

max_out = model.execute(x)[0].to_numpy()

def t(name):
    return torch.from_numpy(arrays[name])

with torch.no_grad():
    y = F.linear(
        torch.from_numpy(x),
        t("remove_tasks_dense1.weight"),
        t("remove_tasks_dense1.bias"),
    )
    a = F.linear(y, t("remove_tasks_act1.w1.weight"))
    b = F.linear(y, t("remove_tasks_act1.w3.weight"))
    pt_out = F.linear(
        F.silu(a) * b,
        t("remove_tasks_act1.w2.weight"),
    ).numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("MATCH:", np.allclose(
    pt_out, max_out, rtol=1e-4, atol=1e-5
))
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
