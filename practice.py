REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:/workspace:ro" \
  localhost/cta-max-faiss:local - <<'PY'
import torch
from collections import Counter

root = "/workspace/artifacts/v1.113/core-artifact"

for filename in ("base_model.pt", "bplan_model.pt"):
    weights = torch.load(
        f"{root}/{filename}",
        map_location="cpu",
        weights_only=True
    )

    if isinstance(weights, dict) and "state_dict" in weights:
        weights = weights["state_dict"]

    print(f"\n=== {filename} ===")
    print("TOTAL PARAMETERS/TENSORS:", len(weights))
    print("COMPONENT GROUPS:")
    print(dict(Counter(k.split(".")[0] for k in weights)))

    print("SELECTED WEIGHTS:")
    terms = (
        "nlp", "context", "sequence", "sibling",
        "moe", "att_pooling", "dense1", "task"
    )
    matches = [
        (k, tuple(v.shape))
        for k, v in weights.items()
        if hasattr(v, "shape")
        and any(term in k.lower() for term in terms)
    ]

    for name, shape in matches[:35]:
        print(name, shape)

    print("MATCHING TENSORS:", len(matches))
PY
