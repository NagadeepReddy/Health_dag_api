python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
source = p.read_text()

old = "model = session.load(graph)"

new = '''# Register existing trained checkpoint weights with MAX.
import torch

checkpoint = Path(
    "artifacts/v1.168/core-artifact/model_0_base.pt"
)
state = torch.load(
    checkpoint, map_location="cpu", weights_only=True
)

if "state_dict" in state:
    state = state["state_dict"]

weights_registry = {}

for name, tensor in state.items():
    if not isinstance(tensor, torch.Tensor):
        continue

    value = tensor.detach().cpu().contiguous().numpy()

    # Keep original checkpoint names.
    weights_registry[name] = value

    # MAX Embedding modules use the name without '.weight'.
    if name.endswith(".weight"):
        weights_registry.setdefault(name[:-7], value)

required = "sequence_transformer.page_embedding"

if required not in weights_registry:
    raise RuntimeError(
        f"Checkpoint has no mapping for {required}"
    )

print("TRAINED CHECKPOINT TENSORS:", len(state))
print("MAX WEIGHT REGISTRY ENTRIES:", len(weights_registry))
print("PAGE EMBEDDING REGISTERED: PASS", flush=True)

model = session.load(
    graph, weights_registry=weights_registry
)'''

if old in source:
    assert source.count(old) == 1
    updated = source.replace(old, new, 1)
    ast.parse(updated)

    backup = p.with_suffix(".py.before_registry_fix")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("MAX WEIGHT REGISTRATION ADDED")
    print("BACKUP:", backup)

elif "PAGE EMBEDDING REGISTERED: PASS" in source:
    print("WEIGHT REGISTRATION ALREADY ADDED")

else:
    raise SystemExit(
        "STOP: Runner differs from expected source"
    )

print("ORIGINAL PYTORCH/DS CODE UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
