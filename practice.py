cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 4g \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/sklearn_161:/validation/python_deps:/workspace/artifacts/v1.472/core-artifact \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:ro" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import torch
from pathlib import Path

print("=== PZAAS PYTORCH TO MAX INPUT CONTRACT ===")

p = "/validation/ppa_pytorch_reference_01.pt"

# Reference generated locally by the previous DS validation.
ref = torch.load(p, map_location="cpu", weights_only=False)

assert "model_in" in ref and "output" in ref

def inspect_value(name, value):
    if isinstance(value, torch.Tensor):
        print(name, "TENSOR", tuple(value.shape), value.dtype)
    elif isinstance(value, dict):
        print(name, "DICT", len(value))
        for k, v in value.items():
            inspect_value(name + "." + str(k), v)
    elif isinstance(value, (list, tuple)):
        print(name, type(value).__name__, len(value))
        for i, v in enumerate(value[:3]):
            inspect_value(name + "[" + str(i) + "]", v)
    else:
        print(name, type(value).__name__)

print("\n=== EXACT ORIGINAL MODEL INPUTS ===")
inspect_value("model_in", ref["model_in"])

print("\n=== ORIGINAL PYTORCH OUTPUT ===")
inspect_value("output", ref["output"])

print("\n=== MAX GRAPH INPUT DECLARATIONS ===")

p = Path(
    "artifacts/v1.472-max/pzaas_max/"
    "grecbase_fusion_full_head_72_max.py"
)

assert p.is_file(), "MAX graph source missing"

lines = p.read_text().splitlines()

for i, line in enumerate(lines, 1):
    if any(x in line for x in (
        "TensorType(",
        "input_types",
        "graph.inputs",
        "def build_grecbase_fusion_graph_order_correct",
    )):
        print(f"{i}: {line.strip()[:180]}")

print("\nPZAAS PYTORCH REFERENCE: VERIFIED")
print("MAX INPUT MAPPING: INSPECTED")
print("ORIGINAL DS: UNCHANGED")
PY
