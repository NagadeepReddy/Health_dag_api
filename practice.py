podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import inspect
import numpy as np
import torch
from pathlib import Path

from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType
from max.graph.weights import WeightData

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")
wdir = base / "grecbase_integration_weights"

# Use the actual PyTorch class, not a reconstructed reference.
sys.path.insert(0, str(root / "utils/dependency-utils"))
from models import ParallelTransformerBlock

params = inspect.signature(ParallelTransformerBlock).parameters
kwargs = {"dim": 256, "dim_head": 256, "heads": 1}
if "ff_mult" in params:
    kwargs["ff_mult"] = 8

pt = ParallelTransformerBlock(**kwargs).eval()

state = torch.load(
    root / "core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True,
    mmap=True,
)
if "state_dict" in state:
    state = state["state_dict"]
elif "model_state_dict" in state:
    state = state["model_state_dict"]

pt_weights = {
    k.removeprefix("att_pooling."): v
    for k, v in state.items()
    if k.startswith("att_pooling.")
}

missing, unexpected = pt.load_state_dict(
    pt_weights, strict=False
)
print("PYTORCH MISSING KEYS:", missing)
print("PYTORCH UNEXPECTED KEYS:", unexpected)
assert not missing and not unexpected, \
    "STOP: original PyTorch attention weights differ"

x = (
    np.random.default_rng(42)
    .standard_normal((1, 8, 256))
    .astype(np.float32) * 0.01
)

with torch.inference_mode():
    output = pt(torch.from_numpy(x))
    if isinstance(output, tuple):
        output = output[0]
    pt_out = output.detach().cpu().numpy()

sys.path.insert(0, str(base))
from att_pooling_max import AttPoolingBlockMAX

cpu = CPU()
device = DeviceRef.from_device(cpu)
block = AttPoolingBlockMAX(
    dtype=DType.float32,
    device=device,
    layer_idx=0,
)

registry = {}
for name in (
    "fused_attn_ff_proj.weight",
    "attn_out.weight",
    "ff_out.1.weight",
):
    key = "att_pooling." + name
    arr = np.load(wdir / (key + ".npy")).astype(np.float32)
    registry[key] = WeightData(
        arr, name=key,
        dtype=DType.float32,
        shape=arr.shape,
    )

inv = np.load(
    wdir / "att_pooling.rotary_emb.inv_freq.npy"
).astype(np.float32)

angles = np.arange(8, dtype=np.float32)[:, None] * inv[None, :]
pos = np.concatenate([angles, angles], axis=-1)
pos = pos[None, None, :, :].astype(np.float32)

graph = Graph(
    "cta_attention_pytorch_parity",
    input_types=[
        TensorType(DType.float32, [1, 8, 256], device=device),
        TensorType(DType.float32, [1, 1, 8, 256], device=device),
    ],
)

with graph:
    graph.output(block(*graph.inputs))

session = InferenceSession(devices=[cpu])
model = session.load(graph, weights_registry=registry)
max_out = model.execute(x, pos)[0].to_numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)

assert pt_out.shape == max_out.shape, \
    "STOP: output shapes differ"

print("MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("MATCH:", np.allclose(
    pt_out, max_out, rtol=1e-4, atol=1e-5
))
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
