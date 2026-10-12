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

names = {
    "page_embedding": "page_embedding_weight.npy",
    "item_embedding": "item_embedding_weight.npy",
    "item_meta_embedding": "item_meta_embedding_weight.npy",
    "item_pre_embedding": "item_pre_embedding_weight.npy",
    "page_meta_wide_dense": "page_meta_wide_dense_weight.npy",
    "page_meta_wide_dense_bias": "page_meta_wide_dense_bias.npy",
}

arrays = {
    key: np.load(base / filename).astype(np.float32)
    for key, filename in names.items()
}

page = np.array([[1, 2, 3, 4]], dtype=np.int64)
item = np.array([[10, 20, 30, 40]], dtype=np.int64)
meta = np.array([[1, 2, 3, 4]], dtype=np.int64)
wide = np.array([[[0.1], [0.2], [-0.3], [0.4]]],
                dtype=np.float32)

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

mapping = {
    "sequence_transformer.page_embedding.weight":
        arrays["page_embedding"],
    "sequence_transformer.item_embedding.weight":
        arrays["item_embedding"],
    "sequence_transformer.item_meta_embedding.weight":
        arrays["item_meta_embedding"],
    "sequence_transformer.item_pre_embedding.weight":
        arrays["item_pre_embedding"],
    "sequence_transformer.page_meta_wide_dense.weight":
        arrays["page_meta_wide_dense"],
    "sequence_transformer.page_meta_wide_dense.bias":
        arrays["page_meta_wide_dense_bias"],
}

registry = {
    key: WeightData(
        value,
        name=key,
        dtype=DType.float32,
        shape=value.shape
    )
    for key, value in mapping.items()
}

session = InferenceSession(devices=[cpu])
model = session.load(graph, weights_registry=registry)

max_out = model.execute(page, item, meta, item, wide)[0].to_numpy()

with torch.no_grad():
    p = F.embedding(
        torch.from_numpy(page),
        torch.from_numpy(arrays["page_embedding"])
    )
    i = F.embedding(
        torch.from_numpy(item),
        torch.from_numpy(arrays["item_embedding"])
    )
    m = F.embedding(
        torch.from_numpy(meta),
        torch.from_numpy(arrays["item_meta_embedding"])
    )
    pre = F.embedding(
        torch.from_numpy(item),
        torch.from_numpy(arrays["item_pre_embedding"])
    )
    pw = F.linear(
        torch.from_numpy(wide),
        torch.from_numpy(arrays["page_meta_wide_dense"]),
        torch.from_numpy(arrays["page_meta_wide_dense_bias"])
    )
    pw = F.leaky_relu(pw, negative_slope=0.2)
    pt_out = torch.cat([p, pw], dim=2) * torch.cat(
        [i, m, pre], dim=2
    )
    pt_out = pt_out.numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("MATCH:", np.allclose(
    pt_out, max_out, rtol=1e-4, atol=1e-5
))
PY
