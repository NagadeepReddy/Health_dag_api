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
src = base / "sibling_context_max.py"
dst = base / "main_context_max.py"
wdir = base / "main_context_weights"

assert src.is_file(), "STOP: verified sibling implementation missing"
assert not dst.exists(), "STOP: main implementation already exists"
assert len(list(wdir.glob("*.npy"))) == 34

s = src.read_text()

replacements = {
    '"sibling_context_weights"': '"main_context_weights"',
    "def sibling_context_forward(": "def main_context_forward(",
    'p = "sibling_context_head"': 'p = "context_head"',
    "for i in range(3)": "for i in range(17)",
    "return ops.concat([deep, wide], axis=1)":
        "return ops.concat([deep, wide], axis=1), embeddings[11]",
}

for old, new in replacements.items():
    assert s.count(old) == 1, f"STOP: source differs: {old}"
    s = s.replace(old, new, 1)

ast.parse(s)
dst.write_text(s)
print("MAIN CONTEXT IMPLEMENTATION CREATED — SYNTAX PASS")

sys.path.insert(0, str(base))
from main_context_max import main_context_forward

def w(name):
    return torch.from_numpy(
        np.load(wdir / (name + ".npy")).astype(np.float32)
    )

def linear(x, name, bias=True):
    return F.linear(
        x, w(name + ".weight"),
        w(name + ".bias") if bias else None
    )

def rms(x, name):
    return x * torch.rsqrt(
        x.square().mean(dim=-1, keepdim=True) + 1e-6
    ) * w(name + ".g")

def swiglu(x, name):
    a = linear(x, name + ".w1", False)
    b = linear(x, name + ".w3", False)
    return linear(F.silu(a) * b, name + ".w2", False)

inputs = [
    np.zeros((1, 1), dtype=np.int64)
    for _ in range(17)
]
inputs.append(
    np.linspace(-0.5, 0.5, 127, dtype=np.float32)
    .reshape(1, 127)
)

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = Graph(
    "cta_main_context_parity",
    input_types=[
        *[
            TensorType(DType.int64, [1, 1], device=device)
            for _ in range(17)
        ],
        TensorType(DType.float32, [1, 127], device=device),
    ],
)

with graph:
    context, extracted = main_context_forward(
        list(graph.inputs[:17]),
        graph.inputs[17],
        device,
    )
    graph.output(context, extracted)

session = InferenceSession(devices=[cpu])
model = session.load(graph)

results = model.execute(*inputs)
max_context = results[0].to_numpy()
max_extracted = results[1].to_numpy()

p = "context_head"

with torch.inference_mode():
    embeddings = [
        F.embedding(
            torch.from_numpy(inputs[i]),
            w(f"{p}.deep_embedding.{i}.weight")
        ).reshape(1, 128)
        for i in range(17)
    ]

    pt_extracted = embeddings[11].numpy()

    deep = torch.cat(embeddings, dim=1)
    deep = F.leaky_relu(deep, negative_slope=0.2)
    deep = rms(deep, p + ".deep_norm")
    deep = swiglu(
        linear(deep, p + ".deep_dense"),
        p + ".deep_swiglu"
    )

    wide = F.batch_norm(
        torch.from_numpy(inputs[17]),
        w(p + ".num_batch_norm.running_mean"),
        w(p + ".num_batch_norm.running_var"),
        w(p + ".num_batch_norm.weight"),
        w(p + ".num_batch_norm.bias"),
        training=False,
        eps=1e-5,
    )

    wide = rms(wide, p + ".wide_norm")
    wide = F.leaky_relu(
        linear(wide, p + ".wide_dense"),
        negative_slope=0.2,
    )
    wide = swiglu(wide, p + ".wide_swiglu")

    pt_context = torch.cat([deep, wide], dim=1).numpy()

print("CONTEXT SHAPE:", max_context.shape)
print("CONTEXT MAX DIFF:",
      np.max(np.abs(pt_context - max_context)))
print("CONTEXT MATCH:", np.allclose(
    pt_context, max_context, rtol=1e-4, atol=1e-5
))

print("EXTRACTED SHAPE:", max_extracted.shape)
print("EXTRACTED MAX DIFF:",
      np.max(np.abs(pt_extracted - max_extracted)))
print("EXTRACTED MATCH:", np.allclose(
    pt_extracted, max_extracted, rtol=1e-4, atol=1e-5
))
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
