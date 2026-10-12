podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import ast
import numpy as np
import torch
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, "artifacts/v1.168/utils/dependency-utils")
from models import ParallelTransformerBlock

# Reuse exact constructor arguments from proven PyTorch runner.
source = ast.parse((base / "run_transformer_parity.py").read_text())
constructors = [
    n.value for n in source.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "pt" for t in n.targets)
    and isinstance(n.value, ast.Call)
    and isinstance(n.value.func, ast.Name)
    and n.value.func.id == "ParallelTransformerBlock"
]
assert len(constructors) == 1, "STOP: constructor differs"
call = constructors[0]
assert not call.args, "STOP: positional constructor arguments"
kwargs = {k.arg: ast.literal_eval(k.value) for k in call.keywords}

checkpoint = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=False
)

blocks = []
for i in (0, 1):
    block = ParallelTransformerBlock(**kwargs)
    prefix = f"sequence_transformer.ptransformer.{i}.fn."
    state = {
        k[len(prefix):]: v
        for k, v in checkpoint.items()
        if k.startswith(prefix)
    }
    block.load_state_dict(state, strict=True)
    block.eval()
    blocks.append(block)

x = torch.from_numpy(np.load(base / "transformer_input.npy")).float()
v1 = torch.tensor([4], dtype=torch.long)

with torch.no_grad():
    x1 = x + blocks[0](x, v1=v1)
    pt_out = (x1 + blocks[1](x1, v1=v1)).numpy()

max_out = np.load(base / "transformer_max_output_2layers.npy")

print("PT SHAPE :", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF :", np.max(np.abs(pt_out - max_out)))
print("MATCH    :", np.allclose(pt_out, max_out, rtol=1e-4, atol=1e-5))
PY
