cd /application1/sajjna8/rt-pzaas-v1.0 && \
OUT="$PWD/artifacts/v1.472-max/pzaas_max/pzaas_base_weights" && \
mkdir -p "$OUT" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none --read-only --memory 3g \
-e PYTHONDONTWRITEBYTECODE=1 \
-v "$PWD/artifacts/v1.472/core-artifact:/model:ro" \
-v "$OUT:/out:rw" \
--entrypoint python3 localhost/cta-max-faiss:local - <<'PY'
import torch, numpy as np, os, shutil, json
from pathlib import Path

out = Path("/out")
if any(out.iterdir()):
    raise SystemExit("STOP: Output directory not empty")

available = 0
for line in Path("/proc/meminfo").read_text().splitlines():
    if line.startswith("MemAvailable:"):
        available = int(line.split()[1]) * 1024

if available < 4 * 1024**3:
    raise SystemExit("RAM GUARD: Need 4 GiB available")

if shutil.disk_usage(out).free < 1024**3:
    raise SystemExit("DISK GUARD: Need 1 GiB free")

state = torch.load(
    "/model/model_0_base.pt",
    map_location="cpu",
    weights_only=True,
    mmap=True
)
if isinstance(state, dict) and isinstance(state.get("state_dict"), dict):
    state = state["state_dict"]

manifest = {}
for name, tensor in state.items():
    if not isinstance(tensor, torch.Tensor):
        continue
    filename = name.replace("/", "__") + ".npy"
    array = tensor.detach().cpu().contiguous().numpy()
    np.save(out / filename, array, allow_pickle=False)
    manifest[name] = {
        "file": filename,
        "shape": list(array.shape),
        "dtype": str(array.dtype)
    }

(out / "manifest.json").write_text(json.dumps(manifest, indent=2))

print("PZAAS WEIGHT EXPORT: PASS")
print("EXPORTED TENSORS:", len(manifest))
print("MODEL:", "v1.472 / model_0_base.pt")
print("ORIGINAL DS: UNCHANGED")
PY
