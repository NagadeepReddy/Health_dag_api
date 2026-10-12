podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import torch
from collections import defaultdict

path = "artifacts/v1.168/core-artifact/model_0_base.pt"

data = torch.load(
    path, map_location="cpu",
    weights_only=True, mmap=True
)

if "state_dict" in data:
    data = data["state_dict"]
elif "model_state_dict" in data:
    data = data["model_state_dict"]

groups = {
    "NLP": ["nlp_encoder", "nlp_dense"],
    "TASK": ["task_embedding"],
    "JET": ["jet_embedding"],
    "IHQ": ["ihq_embedding"],
    "SIBLING": ["sibling_context_head"],
    "ATTENTION": ["att_pooling"],
    "NORMALIZATION": ["moe_norm"],
    "DENSE": ["seq_dense"],
}

for group, patterns in groups.items():
    matches = [
        (k, tuple(v.shape))
        for k, v in data.items()
        if isinstance(v, torch.Tensor)
        and any(
            p in k.lower()
            for p in patterns
        )
        and not k.startswith("sequence_transformer.")
    ]

    print(f"\n===== {group}: {len(matches)} WEIGHTS =====")

    for name, shape in matches[:12]:
        print(name, shape)

    if len(matches) > 12:
        print(f"... {len(matches)-12} additional weights")

print("\nCHECKPOINT INVENTORY COMPLETE")
print("NO FILES MODIFIED")
PY
