cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
-e PYTHONPATH=/application1/sajjna8/rt-pzaas-v1.0/artifacts/v1.472-max \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
from pathlib import Path
import numpy as np
import torch
from max.graph import DeviceRef
from pzaas_max.grecbase_fusion_full_head_72_max import (
    build_grecbase_fusion_graph_order_correct
)

v = Path("artifacts/v1.472-max/pzaas_max/validation")
p = torch.load(
    v / "ppa_model_input_exact.pt",
    map_location="cpu",
    weights_only=True
)
g = build_grecbase_fusion_graph_order_correct(DeviceRef.CPU())

def leaves(x):
    if isinstance(x, dict):
        for value in x.values():
            yield from leaves(value)
    elif isinstance(x, (list, tuple)):
        for value in x:
            yield from leaves(value)
    elif isinstance(x, (torch.Tensor, np.ndarray)):
        yield x

print("=== PZAAS EXACT INPUT ALIGNMENT ===")
print("GRAPH INPUTS:", len(g.inputs))

for name, value in p.items():
    tensors = list(leaves(value))
    shapes = [tuple(t.shape) for t in tensors]
    print(f"{name}: count={len(tensors)}, shapes={shapes[:5]}")

print("=== GRAPH INPUT SIGNATURE ===")
for i, value in enumerate(g.inputs):
    print(i, str(value.type))

print("=== SAVED NUMPY INPUT ARTIFACTS ===")
for path in sorted(v.glob("*.npz")):
    with np.load(path, allow_pickle=False) as data:
        print(path.name, "arrays:", len(data.files))
        print("Keys:", data.files[:20])

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: EXACT 72-INPUT PACKING AND NUMERICAL PARITY")
PY
