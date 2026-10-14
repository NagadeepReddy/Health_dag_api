python3 - <<'PY'
import numpy as np
import torch
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
ckpt = Path("artifacts/v1.168/core-artifact/model_0_base.pt")

state = torch.load(ckpt, map_location="cpu", weights_only=True)
if "state_dict" in state:
    state = state["state_dict"]

for i in (0, 1):
    key = f"sequence_transformer.ptransformer.{i}.fn.norm2.weight"
    file = base / "sequence_weights" / (
        "fn_norm2_g.npy" if i == 0 else "fn_norm2_g_layer1.npy"
    )

    print(f"\n=== TRANSFORMER LAYER {i} ===")
    print("Checkpoint key exists:", key in state)
    print("MAX weight file exists:", file.is_file())

    if key not in state or not file.is_file():
        print("STOP: cannot verify this layer")
        print("Available checkpoint Norm2 keys:",
              [k for k in state if "norm2" in k and "ptransformer" in k])
        continue

    pt = state[key].detach().cpu().numpy()
    mx = np.load(file, allow_pickle=False)

    print("PyTorch shape:", pt.shape)
    print("MAX shape:", mx.shape)

    if pt.shape != mx.shape:
        print("SHAPE MISMATCH")
        continue

    print("MAX_DIFF:", float(np.max(np.abs(pt.astype(np.float64) - mx.astype(np.float64)))))
    print("EXACT MATCH:", bool(np.array_equal(pt, mx)))

print("\nREAD-ONLY VERIFICATION COMPLETE")
PY
