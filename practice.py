podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast, sys
import numpy as np
import torch
import torch.nn.functional as F

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.engine import InferenceSession

base = Path("artifacts/v1.168-max/cta_max")
dst = base / "grecbase_aux_features_max.py"
wdir = base / "grecbase_aux_weights"

assert not dst.exists(), "STOP: auxiliary module already exists"

expected = {
    "task_embedding.0.weight": (2, 128),
    "task_embedding.1.weight": (5, 128),
    "ihq_embedding.weight": (596, 128),
    "jet_embedding.0.weight": (16, 64),
    "jet_embedding.1.weight": (451, 64),
}

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True,
    mmap=True,
)

if "state_dict" in state:
    state = state["state_dict"]
elif "model_state_dict" in state:
    state = state["model_state_dict"]

arrays = {}
for name, shape in expected.items():
    assert name in state, f"STOP: missing {name}"
    arr = state[name].detach().cpu().numpy().astype(np.float32)
    assert arr.shape == shape, f"STOP: shape mismatch {name}"
    assert np.isfinite(arr).all()
    arrays[name] = arr
    if (wdir / (name + ".npy")).exists():
        assert np.array_equal(
            np.load(wdir / (name + ".npy")), arr
        ), f"STOP: existing weight differs: {name}"

code = '''
from pathlib import Path
import numpy as np
from max.dtype import DType
from max.graph import ops

WDIR = Path(__file__).parent / "grecbase_aux_weights"

def grecbase_aux_features(
    task0, task1, ihq_ids, jet_name, jet_status, device
):
    def embed(ids, name):
        arr = np.load(WDIR / (name + ".npy")).astype(np.float32)
        w = ops.constant(arr, dtype=DType.float32, device=device)
        return ops.gather(w, ids, axis=0)

    def pool(x, dim):
        mean = ops.mean(x, axis=1)
        maximum = ops.max(x, axis=1)
        return ops.reshape(
            ops.concat([mean, maximum], axis=1),
            [1, 2 * dim]
        )

    task = ops.concat([
        embed(task0, "task_embedding.0.weight"),
        embed(task1, "task_embedding.1.weight")
    ], axis=2)
    task = ops.reshape(task, [1, 256])

    ihq = pool(embed(ihq_ids, "ihq_embedding.weight"), 128)

    jet0 = pool(embed(jet_name, "jet_embedding.0.weight"), 64)
    jet1 = pool(embed(jet_status, "jet_embedding.1.weight"), 64)

    jet = pool(
        ops.concat([
            ops.reshape(jet0, [1, 1, 128]),
            ops.reshape(jet1, [1, 1, 128])
        ], axis=1),
        128
    )

    return ops.concat([task, ihq, jet], axis=1)
'''

ast.parse(code)

wdir.mkdir(parents=True, exist_ok=True)
for name, arr in arrays.items():
    p = wdir / (name + ".npy")
    if not p.exists():
        np.save(p, arr)

dst.write_text(code)

sys.path.insert(0, str(base))
from grecbase_aux_features_max import grecbase_aux_features

cpu = CPU()
device = DeviceRef.from_device(cpu)

types = [
    TensorType(DType.int64, [1], device=device),
    TensorType(DType.int64, [1], device=device),
    TensorType(DType.int64, [1, 4], device=device),
    TensorType(DType.int64, [1, 4], device=device),
    TensorType(DType.int64, [1, 4], device=device),
]

graph = Graph("cta_grecbase_aux_features", input_types=types)

with graph:
    result = grecbase_aux_features(*graph.inputs, device)
    graph.output(result)

inputs = [
    np.array([1], dtype=np.int64),
    np.array([2], dtype=np.int64),
    np.array([[1, 2, 3, 4]], dtype=np.int64),
    np.array([[1, 2, 3, 4]], dtype=np.int64),
    np.array([[2, 3, 4, 5]], dtype=np.int64),
]

session = InferenceSession(devices=[cpu])
model = session.load(graph)
max_out = model.execute(*inputs)[0].to_numpy()

def tw(name):
    return torch.from_numpy(arrays[name])

def pt_pool(x):
    return torch.cat(
        [x.mean(dim=1), x.max(dim=1).values],
        dim=1
    )

with torch.no_grad():
    t0 = F.embedding(torch.from_numpy(inputs[0]), tw("task_embedding.0.weight"))
    t1 = F.embedding(torch.from_numpy(inputs[1]), tw("task_embedding.1.weight"))
    task = torch.cat([t0, t1], dim=1)

    ihq = pt_pool(
        F.embedding(torch.from_numpy(inputs[2]), tw("ihq_embedding.weight"))
    )

    j0 = pt_pool(
        F.embedding(torch.from_numpy(inputs[3]), tw("jet_embedding.0.weight"))
    )
    j1 = pt_pool(
        F.embedding(torch.from_numpy(inputs[4]), tw("jet_embedding.1.weight"))
    )
    jet = pt_pool(torch.stack([j0, j1], dim=1))

    pt_out = torch.cat([task, ihq, jet], dim=1).numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("MATCH:", np.allclose(
    pt_out, max_out, rtol=1e-4, atol=1e-5
))
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
