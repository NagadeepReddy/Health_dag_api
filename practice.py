python3 - <<'PY'
import torch
import numpy as np
from pathlib import Path

base = Path("artifacts/v1.168")
ckpt = torch.load(base/"core-artifact/model_0_base.pt",
                  map_location="cpu", weights_only=True)
state = ckpt.get("state_dict", ckpt)
weights = base.parent/"v1.168-max/cta_max/sequence_weights"

for name in ("seq_dense.weight", "seq_dense.bias",
             "sequence_transformer.seq_dense.weight",
             "sequence_transformer.seq_dense.bias"):
    print("\n", name)
    if name not in state:
        print("CHECKPOINT KEY MISSING")
        continue
    original = state[name].detach().cpu().numpy()
    print("Checkpoint shape:", original.shape)
    exported = weights/(name.split(".")[-2]+"."+name.split(".")[-1]+".npy")
    if name.startswith("sequence_transformer."):
        print("Internal layer uses checkpoint registration")
        continue
    if exported.exists():
        actual = np.load(exported, allow_pickle=False)
        print("MAX export shape:", actual.shape)
        print("MATCH:", np.array_equal(original, actual))
        if original.shape == actual.shape:
            print("MAX DIFF:", np.max(np.abs(original-actual)))
    else:
        print("MAX export MISSING:", exported)
PY
