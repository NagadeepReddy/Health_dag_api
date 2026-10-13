podman run --rm -i -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import ast
import torch

root = Path("artifacts/v1.168")
source_file = root / "utils/dependency-utils/models.py"
input_file = Path(
    "artifacts/v1.168-max/cta_max/real_sanity_model_in.pt"
)

print("=== ORIGINAL PYTORCH POOLING DEFINITIONS ===")

source = source_file.read_text()
tree = ast.parse(source)

found = False
for node in ast.walk(tree):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Attribute) and target.attr in (
                "ihq_pooling", "jet_pooling"
            ):
                print(f"LINE {node.lineno}:",
                      ast.get_source_segment(source, node))
                found = True

if not found:
    print("POOLING ASSIGNMENTS NOT FOUND")

print("\n=== SAVED REAL PYTORCH MODEL INPUTS ===")

data = torch.load(
    input_file, map_location="cpu", weights_only=True
)

names = [
    "deep_in", "page_in", "item_in", "item_meta_in",
    "page_meta_wide_in", "v1_in", "task_in", "tf_name_in",
    "sibling_wide_in", "sibling_deep_in",
    "sibling_item_wide_in", "sibling_item_in",
    "current_in", "current_meta_in", "wide_in",
    "input_ids", "attention_mask"
]

def describe(x):
    if isinstance(x, torch.Tensor):
        return f"Tensor {tuple(x.shape)} {x.dtype}"
    if isinstance(x, dict):
        return "dict " + str({
            k: describe(v) for k, v in list(x.items())[:20]
        })
    if isinstance(x, (list, tuple)):
        return (
            f"{type(x).__name__}[{len(x)}] "
            + str([describe(v) for v in x[:20]])
        )
    return type(x).__name__

print("SAVED OBJECT:", type(data).__name__)

if isinstance(data, (list, tuple)):
    print("INPUT COUNT:", len(data))
    for i, value in enumerate(data):
        name = names[i] if i < len(names) else f"extra_{i}"
        print(f"{i:02d} {name}: {describe(value)}")
elif isinstance(data, dict):
    for key, value in data.items():
        print(key, describe(value))
else:
    print(describe(data))

print("\nREAD ONLY — ORIGINAL CODE AND SAVED FILES UNCHANGED")
PY
