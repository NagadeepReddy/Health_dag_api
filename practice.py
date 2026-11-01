REPO=/application1/sajjna8/rt-pzai-bplan-v1
OUT="$REPO/artifacts/v1.113-max/maxserve_bplan_extension"

grep -qxF 'max_weights/' "$OUT/.gitignore" 2>/dev/null || echo 'max_weights/' >> "$OUT/.gitignore"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:/bplan:ro" \
  -v "$OUT:/bplan_out:rw" \
  localhost/cta-max-faiss:local - <<'PY'
import torch, numpy as np, json, shutil
from pathlib import Path

src = Path("/bplan/artifacts/v1.113/core-artifact/base_model.pt")
dst = Path("/bplan_out/max_weights")
dst.mkdir(exist_ok=True)

weights = torch.load(src, map_location="cpu", weights_only=True)
assert len(weights) == 208

required = sum(t.numel() * t.element_size() for t in weights.values())
assert shutil.disk_usage(dst).free > required * 2, "Insufficient disk space"

manifest = {}

for name, tensor in sorted(weights.items()):
    arr = tensor.detach().cpu().numpy()
    np.save(dst / f"{name}.npy", arr, allow_pickle=False)
    manifest[name] = {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype)
    }

(dst / "manifest.json").write_text(json.dumps(manifest, indent=2))

assert len(list(dst.glob("*.npy"))) == 208

print("BPLAN MAX WEIGHT EXPORT: PASS")
print("EXPORTED TENSORS:", len(manifest))
print("LOCATION:", dst)
print("ORIGINAL CHECKPOINT: UNCHANGED")
PY
