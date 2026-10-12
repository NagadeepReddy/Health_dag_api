podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import numpy as np
import torch
from pathlib import Path

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.engine import InferenceSession

sys.path.insert(0, "artifacts/v1.168/utils/dependency-utils")
import models

sys.path.insert(0, "artifacts/v1.168-max/cta_max")
import att_pooling_max

assert hasattr(models, "apply_rotary_pos_emb"), \
    "STOP: original rotary function unavailable"
assert hasattr(att_pooling_max, "apply_rotary_pos_emb_max"), \
    "STOP: MAX rotary function unavailable"

pt = models.ParallelTransformerBlock(
    dim=256, dim_head=256, heads=1, ff_mult=4
).eval()

positions = pt.get_rotary_embedding(8, torch.device("cpu"))

q = np.random.default_rng(42).standard_normal(
    (1, 1, 8, 256)
).astype(np.float32)

with torch.inference_mode():
    pt_out = models.apply_rotary_pos_emb(
        positions, torch.from_numpy(q)
    ).numpy()

pos = positions.detach().numpy()[None, None, :, :].astype(np.float32)

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = Graph(
    "cta_rotary_application_diagnostic",
    input_types=[
        TensorType(DType.float32, [1, 1, 8, 256], device=device),
        TensorType(DType.float32, [1, 1, 8, 256], device=device),
    ],
)

with graph:
    result = att_pooling_max.apply_rotary_pos_emb_max(
        graph.inputs[1], graph.inputs[0]
    )
    graph.output(result)

session = InferenceSession(devices=[cpu])
model = session.load(graph)
max_out = model.execute(q, pos)[0].to_numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("ROTARY MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("ROTARY MATCH:", np.allclose(
    pt_out, max_out, rtol=1e-4, atol=1e-5
))
print("NO FILES MODIFIED")
PY
