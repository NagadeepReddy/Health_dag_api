cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none --read-only \
-e PYTHONDONTWRITEBYTECODE=1 \
-v "$PWD/artifacts/v1.472/core-artifact:/model:ro" \
--entrypoint python3 localhost/cta-max-faiss:local - <<'PY'
import torch

print("PyTorch:", torch.__version__, flush=True)

p = "/model/model_0_base.pt"
try:
    state = torch.load(
        p, map_location="meta",
        weights_only=True, mmap=True
    )
except Exception as e:
    raise SystemExit(f"ERROR: {type(e).__name__}: {e}")

if isinstance(state, dict) and isinstance(state.get("state_dict"), dict):
    state = state["state_dict"]

print("TOTAL ENTRIES:", len(state))

for k, v in state.items():
    if hasattr(v, "shape") and any(
        x in k.lower()
        for x in ("seq", "dense", "nlp", "sibling", "task")
    ):
        print(k, tuple(v.shape))

print("PZAAS CHECKPOINT METADATA: PASS")
PY
