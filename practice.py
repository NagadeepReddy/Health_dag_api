set -e

python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/grecbase_aux_features_max.py")
s = p.read_text()

old = '''task = ops.concat([
        embed(task0, "task_embedding.0.weight"),
        embed(task1, "task_embedding.1.weight")
    ], axis=2)'''

new = old.replace("], axis=2)", "], axis=1)")

assert s.count(old) == 1, "STOP: existing task implementation differs"

updated = s.replace(old, new, 1)
ast.parse(updated)
p.write_text(updated)

print("TASK CONCAT AXIS CORRECTED")
print("SYNTAX PASS")
PY

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.engine import InferenceSession

base = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, str(base))

from grecbase_aux_features_max import grecbase_aux_features

wdir = base / "grecbase_aux_weights"

def weight(name):
    return np.load(wdir / (name + ".npy")).astype(np.float32)

names = [
    "task_embedding.0.weight",
    "task_embedding.1.weight",
    "ihq_embedding.weight",
    "jet_embedding.0.weight",
    "jet_embedding.1.weight",
]
weights = {n: torch.from_numpy(weight(n)) for n in names}

inputs = [
    np.array([1], dtype=np.int64),
    np.array([2], dtype=np.int64),
    np.array([[1, 2, 3, 4]], dtype=np.int64),
    np.array([[1, 2, 3, 4]], dtype=np.int64),
    np.array([[2, 3, 4, 5]], dtype=np.int64),
]

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = Graph(
    "cta_aux_features_corrected",
    input_types=[
        TensorType(DType.int64, list(x.shape), device=device)
        for x in inputs
    ],
)

with graph:
    result = grecbase_aux_features(*graph.inputs, device)
    graph.output(result)

session = InferenceSession(devices=[cpu])
model = session.load(graph)
max_out = model.execute(*inputs)[0].to_numpy()

def embed(index, name):
    return F.embedding(
        torch.from_numpy(inputs[index]), weights[name]
    )

def pool(x):
    return torch.cat([x.mean(1), x.max(1).values], dim=1)

with torch.no_grad():
    task = torch.cat([
        embed(0, names[0]),
        embed(1, names[1])
    ], dim=1)

    ihq = pool(embed(2, names[2]))
    jet0 = pool(embed(3, names[3]))
    jet1 = pool(embed(4, names[4]))
    jet = pool(torch.stack([jet0, jet1], dim=1))

    pt_out = torch.cat([task, ihq, jet], dim=1).numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("MATCH:", np.allclose(pt_out, max_out, rtol=1e-4, atol=1e-5))
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
