podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v /application1/sajjna8/rt-pzai-bplan-v1:/workspace:ro \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import torch; from pathlib import Path
base = Path("/workspace/artifacts/v1.113/core-artifact")
for name in ("base_model.pt", "bplan_model.pt"):
    print("\n===", name, "===")
    state = torch.load(base/name, map_location="cpu", weights_only=True)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    matches = [(k, tuple(v.shape)) for k, v in state.items()
               if hasattr(v, "shape") and ("norm1" in k.lower() or "att_pooling" in k.lower())]
    for key, shape in matches[:50]:
        print(key, shape)
    print("MATCHES:", len(matches))'
