cat > artifacts/v1.168-max/cta_max/run_transformer_max.py <<'PY'
import sys
import numpy as np

from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef
from max.graph.weights import WeightData
from max.graph import Shape

sys.path.insert(0, "artifacts/v1.168-max/cta_max")
from parallel_transformer_graph import build_parallel_transformer_graph

BASE = "artifacts/v1.168-max/cta_max"
WBASE = BASE + "/sequence_weights"

device = CPU()
device_ref = DeviceRef.from_device(device)

# Same explicit WeightData registry pattern already proven in ContextHead.
weight_files = {
    "sequence_transformer.ptransformer.0.norm1.weight":
        WBASE + "/sequence_transformer.ptransformer.0.fn.norm1.g.npy",

    "sequence_transformer.ptransformer.0.norm2.weight":
        WBASE + "/sequence_transformer.ptransformer.0.fn.norm2.g.npy",

    "sequence_transformer.ptransformer.0.fused_attn_ff_proj.weight":
        WBASE + "/sequence_transformer.ptransformer.0.fn.fused_attn_ff_proj.weight.npy",

    "sequence_transformer.ptransformer.0.attn_out.weight":
        WBASE + "/sequence_transformer.ptransformer.0.fn.attn_out.weight.npy",

    "sequence_transformer.ptransformer.0.ff_out.1.weight":
        WBASE + "/sequence_transformer.ptransformer.0.fn.ff_out.1.weight.npy",
}

weights = {}

for name, path in weight_files.items():
    arr = np.load(path).astype(np.float32)
    weights[name] = WeightData(
        arr=arr,
        dtype=DType.float32,
        shape=Shape(arr.shape),
    )

graph = build_parallel_transformer_graph(
    device_ref=device_ref,
    weights_registry=weights,
)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

x = np.load(BASE + "/transformer_input.npy").astype(np.float32)

# Exact rotary math from the original CTA implementation.
inv_freq = np.load(
    WBASE + "/sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq.npy"
).astype(np.float32)

seq = np.arange(x.shape[1], dtype=np.float32)
freqs = np.einsum("i,j->ij", seq, inv_freq)
pos = np.concatenate([freqs, freqs], axis=-1)
pos = pos[None, None, :, :].astype(np.float32)

out = model.execute(x, pos)[0]
max_out = np.asarray(out)

np.save(BASE + "/transformer_max_output.npy", max_out)

pt_out = np.load(BASE + "/transformer_pytorch_output.npy")

print("PT SHAPE :", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF :", np.max(np.abs(pt_out - max_out)))
print("MATCH    :", np.allclose(pt_out, max_out, rtol=1e-4, atol=1e-5))
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_max.py
