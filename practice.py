cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)
ROOT=/application1/sajjna8/rt-pzaas-v1.0
IMAGE=""

echo "=== PZAAS PYTORCH RUNTIME RECOVERY ==="

for CID in 87202aa5f06a 225c544812ad 393fc64b1a75 d8578435c7b; do
    IMG=$("${P[@]}" inspect --format '{{.Image}}' "$CID" 2>/dev/null || true)

    if [ -n "$IMG" ] && "${P[@]}" image exists "$IMG"; then
        IMAGE="$IMG"
        echo "EXISTING PYTORCH IMAGE: FOUND"
        break
    fi
done

if [ -z "$IMAGE" ]; then
    echo "BLOCKED: Previously verified PyTorch image unavailable"
    exit 1
fi

"${P[@]}" run --rm -i \
    --network none \
    --read-only \
    --tmpfs /tmp:rw,size=1g \
    -e HOME=/tmp \
    -e XDG_CACHE_HOME=/tmp \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$ROOT:$ROOT:ro" \
    -w "$ROOT" \
    --entrypoint /opt/venv/bin/python \
    "$IMAGE" - <<'PY'
from pathlib import Path
import torch

print("=== PZAAS ORIGINAL PYTORCH REFERENCES ===")
print("TORCH:", torch.__version__)

root = Path.cwd()
base = root / "artifacts/v1.472-max/pzaas_max/validation"

files = [
    "ppa_model_input_exact.pt",
    "ppa_pytorch_reference_01.pt",
    "ppa_model_base_reference.pt",
]

for name in files:
    path = base / name
    if not path.is_file():
        raise RuntimeError(f"Missing reference: {path}")

    obj = torch.load(
        path,
        map_location="cpu",
        weights_only=True,
    )

    print("REFERENCE LOADED:", name)

    if isinstance(obj, torch.Tensor):
        print("SHAPE:", tuple(obj.shape))

    elif isinstance(obj, dict):
        print("KEYS:", list(obj.keys()))

        if "model_in" in obj:
            print("MODEL INPUT: FOUND")

        if "output" in obj:
            print("PYTORCH OUTPUT: FOUND")

print("PYTORCH RUNTIME: PASS")
print("SAVED REFERENCES: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: REPLAY ORIGINAL PYTORCH MODEL")
PY
SH
