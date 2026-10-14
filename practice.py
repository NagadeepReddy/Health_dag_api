python3 - <<'PY'
from pathlib import Path
import numpy as np

b = Path("artifacts/v1.168-max/cta_max")
files = {
    "Original Sequence output": b / "sequence_real_full_output.npy",
    "Verified PyTorch": b / "real_sanity_pytorch_same_input_verified.npz",
    "Saved MAX branches": b / "real_sanity_max_branches.npz",
}
arrays = {}

for label, path in files.items():
    if not path.exists():
        print(label, "MISSING")
        continue
    with np.load(path, allow_pickle=False) as data:
        if isinstance(data, np.ndarray):
            arrays[label] = data
        elif "sequence" in data.files:
            arrays[label] = data["sequence"]
    if label in arrays:
        print(label, arrays[label].shape)

print("\n=== SEQUENCE COMPARISON ===")
names = list(arrays)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, c = arrays[names[i]], arrays[names[j]]
        if a.shape == c.shape:
            print(names[i], "vs", names[j],
                  "MAX DIFF:", np.max(np.abs(a.astype(np.float64)-c.astype(np.float64))))
        else:
            print(names[i], "vs", names[j], "SHAPE DIFFERS")
PY
