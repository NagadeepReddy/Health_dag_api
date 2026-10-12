podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np
import torch

base = Path("artifacts/v1.168-max/cta_max")
ckpt = Path("artifacts/v1.168/core-artifact/model_0_base.pt")

existing = list(base.rglob("remove_tasks_dense1.weight.npy"))
assert len(existing) == 1, f"Expected one existing export, found {len(existing)}"

target = existing[0].parent
reference = np.load(existing[0])

print("Loading original checkpoint...")
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
    key for key, value in tensors.items()
    if key.endswith("remove_tasks_dense1.weight")
    and tuple(value.shape) == reference.shape
    and np.array_equal(value.numpy(), reference)
]

if len(matches) != 1:
    print("CHECKPOINT MATCH NOT UNIQUE:", len(matches))
    print("No files exported.")
    raise SystemExit(1)

prefix = matches[0][:-len("remove_tasks_dense1.weight")]
print("Existing exported weights match checkpoint: YES")

names = [
    "remove_tasks_dense2.weight",
    "remove_tasks_dense2.bias",
]

for name in names:
    if prefix + name not in tensors:
        print("MISSING CHECKPOINT KEY:", prefix + name)
        raise SystemExit(1)

for name in names:
    array = tensors[prefix + name].numpy().astype(np.float32)
    destination = target / (name + ".npy")
    if destination.exists():
        print("ALREADY EXISTS:", destination.name, array.shape)
    else:
        np.save(destination, array)
        print("EXPORTED:", destination.name, array.shape)

print("ORIGINAL PYTORCH AND DS FILES UNCHANGED")
PY
