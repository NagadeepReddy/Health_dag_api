podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
import numpy as np
import torch

base = Path("artifacts/v1.168-max/cta_max")
dst = base / "grecbase_integration_weights"

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True,
    mmap=True
)

if "state_dict" in state:
    state = state["state_dict"]
elif "model_state_dict" in state:
    state = state["model_state_dict"]

expected = {
    "att_pooling.norm1.g": (256,),
    "att_pooling.norm2.g": (2048,),
    "att_pooling.rotary_emb.inv_freq": (128,),
    "att_pooling.fused_attn_ff_proj.weight": (2816, 256),
    "att_pooling.attn_out.weight": (256, 256),
    "att_pooling.ff_out.1.weight": (256, 1024),
    "moe_norm1.g": (256,),
    "moe_norm2.g": (256,),
    "seq_dense.weight": (256, 256),
    "seq_dense.bias": (256,),
}

prepared = {}

for name, shape in expected.items():
    assert name in state, f"STOP: missing {name}"
    arr = state[name].detach().cpu().numpy().astype(np.float32)
    assert arr.shape == shape, f"STOP: shape mismatch {name}"
    assert np.isfinite(arr).all(), f"STOP: invalid {name}"
    prepared[name] = arr

    path = dst / (name + ".npy")
    if path.exists():
        assert np.array_equal(np.load(path), arr), \
            f"STOP: existing weight differs: {name}"

dst.mkdir(parents=True, exist_ok=True)

for name, arr in prepared.items():
    path = dst / (name + ".npy")
    if not path.exists():
        np.save(path, arr)
    print("READY:", name, arr.shape)

print("\nALL 10 GRecBase INTEGRATION WEIGHTS READY")

p = base / "parallel_transformer_block_2layers.py"
source = p.read_text()
tree = ast.parse(source)

matches = [
    n for n in tree.body
    if isinstance(n, ast.ClassDef)
    and n.name == "ParallelTransformerBlockMAX"
]

assert len(matches) == 1, "STOP: existing MAX block not found"

print("\n===== EXISTING MAX ATTENTION BLOCK =====")

for node in matches[0].body:
    if isinstance(node, ast.FunctionDef) and node.name in (
        "__init__", "__call__"
    ):
        print(ast.get_source_segment(source, node))

print("\nORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
