python3 - <<'PY'
from pathlib import Path
import numpy as np

b = Path("artifacts/v1.168-max/cta_max")
files = {
    "Original Sequence": b / "sequence_real_full_output.npy",
    "Verified PyTorch": b / "real_sanity_pytorch_same_input_verified.npz",
    "Saved MAX": b / "real_sanity_max_branches.npz",
}

arrays = {}

for name, path in files.items():
    if not path.exists():
        print(name, "MISSING")
        continue

    if path.suffix == ".npy":
        arrays[name] = np.load(path, allow_pickle=False)
    else:
        with np.load(path, allow_pickle=False) as data:
            if "sequence" in data.files:
                arrays[name] = data["sequence"].copy()
            else:
                print(name, "Sequence key missing")
                continue

    print(name, "shape:", arrays[name].shape)

print("\n=== SEQUENCE COMPARISON ===")

names = list(arrays)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a = arrays[names[i]]
        c = arrays[names[j]]

        if a.shape == c.shape:
            diff = np.max(np.abs(
                a.astype(np.float64) - c.astype(np.float64)
            ))
            print(names[i], "vs", names[j], "MAX DIFF:", diff)
        else:
            print(names[i], "vs", names[j], "SHAPE DIFFERENCE")
PY
