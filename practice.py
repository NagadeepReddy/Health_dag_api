cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 3g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
--tmpfs /tmp:rw,size=256m \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:ro" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import torch
from pathlib import Path

print("=== PZAAS MAX INPUT CONTRACT VALIDATION ===")

ref = torch.load(
    "/validation/ppa_pytorch_reference_01.pt",
    map_location="cpu",
    weights_only=False
)

model_in = ref["model_in"]
output = ref["output"]

print("\n=== ORIGINAL PYTORCH INPUTS ===")

total = 0

def inspect(name, value):
    global total
    if isinstance(value, torch.Tensor):
        total += 1
        return
    if isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            inspect(f"{name}[{i}]", v)

for name, value in model_in.items():
    before = total
    inspect(name, value)
    print(
        name,
        "| type:", type(value).__name__,
        "| tensors:", total - before
    )

print("\nTOTAL INPUT FIELDS:", len(model_in))
print("TOTAL LEAF TENSORS:", total)
print("PYTORCH OUTPUT TYPE:", type(output).__name__)
print("PYTORCH OUTPUT COUNT:",
      len(output) if hasattr(output, "__len__") else "N/A")

print("\n=== MAX GRAPH DECLARATION ===")

p = Path(
    "artifacts/v1.472-max/pzaas_max/"
    "grecbase_fusion_full_head_72_max.py"
)

assert p.is_file(), "MAX graph file missing"

lines = p.read_text().splitlines()

for n in range(17, min(32, len(lines) + 1)):
    print(f"{n}: {lines[n-1]}")

print("\n=== ORIGINAL DS INFERENCE MAPPING ===")

p = Path("artifacts/v1.472/core-artifact/pipeline.py")
lines = p.read_text().splitlines()

for n in range(4730, 4790):
    print(f"{n}: {lines[n-1][:180]}")

print("\nINPUT CONTRACT INSPECTION: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
