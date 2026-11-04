cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
-v "$PWD:/workspace" -w /workspace \
--entrypoint python \
localhost/cta-max-faiss:local - <<'PY'
from pathlib import Path
import torch, re

root = Path("artifacts/v1.472-max/pzaas_max/validation")
files = [
    "ppa_model_base_reference.pt",
    "ppa_pytorch_reference_01.pt",
    "ppa_model_input_exact.pt"
]

found = {}

def scan(obj, prefix=""):
    if isinstance(obj, torch.nn.Module):
        scan(obj.state_dict(), prefix)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if torch.is_tensor(v):
                match = re.search(r"ptransformer\.(\d+)\.", key)
                if match and int(match.group(1)) in range(2, 6):
                    found[key] = v.detach().cpu()
            elif isinstance(v, (dict, torch.nn.Module)):
                scan(v, key)

print("=== PZAAS RUNTIME WEIGHT RECOVERY ===")

for name in files:
    path = root / name
    if not path.is_file():
        continue
    data = torch.load(path, map_location="cpu", weights_only=False)
    scan(data)
    print("REFERENCE:", name, "READ")

layers = sorted({
    int(re.search(r"ptransformer\.(\d+)\.", k).group(1))
    for k in found
})

print("RECOVERED LAYERS:", layers)
print("RECOVERED TENSORS:", len(found))

if layers == [2, 3, 4, 5]:
    target = root / "runtime_layers_2_to_5.pt"
    torch.save(found, target)
    print("RUNTIME LAYERS: RECOVERED")
    print("SAVED:", target)
    print("NEXT: ALIGN MAX WEIGHTS AND TEST PARITY")
else:
    print("RUNTIME LAYERS: NOT PRESENT IN SAVED REFERENCES")
    print("NEXT: CAPTURE INITIALIZED LAYERS FROM ORIGINAL DS LOADER")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
