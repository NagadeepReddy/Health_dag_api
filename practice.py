podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np
import torch
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "grecbase_get_path_max.py"
ckpt = Path("artifacts/v1.168/core-artifact/model_0_base.pt")

existing = list(base.rglob("remove_tasks_dense1.weight.npy"))
assert len(existing) == 1, "Cannot uniquely locate existing weights"

weights_dir = existing[0].parent
reference = np.load(existing[0])

data = torch.load(ckpt, map_location="cpu", weights_only=True)
tensors = {}

def collect(obj, prefix=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            name = prefix + str(key)
            if isinstance(value, torch.Tensor):
                tensors[name] = value.detach().cpu()
            elif isinstance(value, dict):
                collect(value, name + ".")

collect(data)

matches = [
    k for k, v in tensors.items()
    if k.endswith("remove_tasks_dense1.weight")
    and tuple(v.shape) == reference.shape
    and np.array_equal(v.numpy(), reference)
]
assert len(matches) == 1, "Checkpoint verification failed"

prefix = matches[0][:-len("remove_tasks_dense1.weight")]
key = prefix + "remove_tasks_dense2.weight"
assert key in tensors, "Final projection missing from checkpoint"

arr = tensors[key].numpy().astype(np.float32)
assert arr.shape == (10819, 2048), arr.shape

text = src.read_text()
old = 'return linear(activated * b, "remove_tasks_act1.w2")'
new = (
    'hidden = linear(activated * b, "remove_tasks_act1.w2")\n'
    '    return linear(hidden, "remove_tasks_dense2")'
)

assert text.count(old) == 1, "Unexpected MAX source; no changes made"
updated = text.replace(old, new)
ast.parse(updated)

destination = weights_dir / "remove_tasks_dense2.weight.npy"
if destination.exists():
    assert np.array_equal(np.load(destination), arr), "Existing weight mismatch"
else:
    np.save(destination, arr)

src.write_text(updated)

print("CHECKPOINT VERIFIED: YES")
print("FINAL WEIGHT:", arr.shape)
print("GET_PATH FINAL PROJECTION ADDED")
print("MAX SOURCE SYNTAX: PASS")
print("ORIGINAL PYTORCH AND DS FILES UNCHANGED")
PY
