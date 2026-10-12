podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import numpy as np
import torch
import torch.nn.functional as F
from pathlib import Path

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.graph.weights import WeightData
from max.engine import InferenceSession

sys.path.insert(0, "artifacts/v1.168-max")
from cta_max.sequence_transformer_max import ParallelTransformerMAEPMAX

base = Path("artifacts/v1.168-max/cta_max/sequence_weights")

def load(name):
    return np.load(base / name).astype(np.float32)

p_w = load("page_embedding_weight.npy")
i_w = load("item_embedding_weight.npy")
m_w = load("item_meta_embedding_weight.npy")
pre_w = load("item_pre_embedding_weight.npy")
wide_w = load("page_meta_wide_dense_weight.npy")
wide_b = load("page_meta_wide_dense_bias.npy")

page = np.array([[1, 2, 3, 4]], dtype=np.int64)
item = np.array([[10, 20, 30, 40]], dtype=np.int64)
meta = np.array([[1, 2, 3, 4]], dtype=np.int64)
wide = np.array(
    [[[0.1], [0.2], [-0.3], [0.4]]],
    dtype=np.float32
)

cpu = CPU()
device = DeviceRef.from_device(cpu)

module = ParallelTransformerMAEPMAX(
    dtype=DType.float32,
    device=device
)

graph = Graph(
    "cta_real_sequence_features",
    input_types=[
        TensorType(DType.int64, [1, 4], device=device),
        TensorType(DType.int64, [1, 4], device=device),
        TensorType(DType.int64, [1, 4], device=device),
        TensorType(DType.int64, [1, 4], device=device),
        TensorType(DType.float32, [1, 4, 1], device=device),
    ],
)

with graph:
    result = module(*graph.inputs)
    graph.output(result)

# MAX Embedding keys have NO .weight suffix.
# MAX Linear keys retain .weight and .bias.
mapping = {
    "sequence_transformer.page_embedding": p_w,
    "sequence_transformer.item_embedding": i_w,
    "sequence_transformer.item_meta_embedding": m_w,
    "sequence_transformer.item_pre_embedding": pre_w,
    "sequence_transformer.page_meta_wide_dense.weight": wide_w,
    "sequence_transformer.page_meta_wide_dense.bias": wide_b,
}

registry = {
    name: WeightData(
        arr,
        name=name,
        dtype=DType.float32,
        shape=arr.shape
    )
    for name, arr in mapping.items()
}

session = InferenceSession(devices=[cpu])
model = session.load(graph, weights_registry=registry)

max_out = model.execute(
    page, item, meta, item, wide
)[0].to_numpy()

with torch.no_grad():
    p = F.embedding(torch.from_numpy(page), torch.from_numpy(p_w))
    i = F.embedding(torch.from_numpy(item), torch.from_numpy(i_w))
    m = F.embedding(torch.from_numpy(meta), torch.from_numpy(m_w))
    pre = F.embedding(torch.from_numpy(item), torch.from_numpy(pre_w))

    pw = F.linear(
        torch.from_numpy(wide),
        torch.from_numpy(wide_w),
        torch.from_numpy(wide_b)
    )
    pw = F.leaky_relu(pw, negative_slope=0.2)

    pt_out = (
        torch.cat([p, pw], dim=2) *
        torch.cat([i, m, pre], dim=2)
    ).numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("MATCH:", np.allclose(
    pt_out, max_out, rtol=1e-4, atol=1e-5
))
PY
