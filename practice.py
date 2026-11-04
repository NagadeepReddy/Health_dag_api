cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 3g \
-e PYTHONDONTWRITEBYTECODE=1 \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import ast
import json
import os
import re
from pathlib import Path
import torch

os.umask(0o077)

print("=== PZAAS EXACT MAX ALIGNMENT ===")

ref = torch.load(
    "/validation/ppa_pytorch_reference_01.pt",
    map_location="cpu",
    weights_only=True
)

model_in = ref["model_in"]
assert isinstance(model_in, dict)

inputs = []

def flatten(path, value):
    if isinstance(value, torch.Tensor):
        inputs.append({
            "path": path,
            "shape": list(value.shape),
            "dtype": str(value.dtype)
        })
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            flatten(f"{path}[{i}]", item)
    elif isinstance(value, dict):
        for key, item in value.items():
            flatten(f"{path}.{key}", item)

for key, value in model_in.items():
    flatten(key, value)

source_path = Path(
    "artifacts/v1.472/utils/dependency-utils/models.py"
)
source = source_path.read_text()
tree = ast.parse(source)

classes = [
    n for n in tree.body
    if isinstance(n, ast.ClassDef)
    and n.name == "GRecBase"
]

assert len(classes) == 1, "Expected one GRecBase class"

forward = next(
    n for n in classes[0].body
    if isinstance(n, ast.FunctionDef)
    and n.name == "forward"
)

args = [
    a.arg for a in forward.args.args
    if a.arg != "self"
]

graph_path = Path(
    "artifacts/v1.472-max/pzaas_max/"
    "grecbase_fusion_full_head_72_max.py"
)

graph_source = graph_path.read_text()

match = re.search(
    r'Graph\(\s*["\']([^"\']+)',
    graph_source
)

graph_name = match.group(1) if match else "UNKNOWN"

manifest = {
    "model_class": "GRecBase",
    "reference": "ppa_pytorch_reference_01.pt",
    "forward_arguments": args,
    "original_input_fields": list(model_in),
    "leaf_tensors": inputs,
    "existing_max_graph": graph_name
}

target = Path("/validation/pzaas_alignment_manifest.json")

target.write_text(json.dumps(manifest, indent=2))
target.chmod(0o600)

print("MODEL CLASS: GRecBase")
print("ORIGINAL INPUT FIELDS:", len(model_in))
print("ORIGINAL LEAF TENSORS:", len(inputs))
print("FORWARD ARGUMENTS:", len(args))
print("MAX GRAPH NAME:", graph_name)

print("\n=== INPUT GROUPS ===")
for key, value in model_in.items():
    count = sum(
        x["path"] == key
        or x["path"].startswith(key + "[")
        or x["path"].startswith(key + ".")
        for x in inputs
    )
    print(key, "=>", count, "tensors")

print("\nALIGNMENT MANIFEST: SAVED")
print("PATH:", target)
print("ORIGINAL DS: UNCHANGED")
print("MAX GRAPH: UNCHANGED")
print("PZAAS GRAPH ALIGNMENT: NEXT")
PY
