python - <<'PY'
from pathlib import Path
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")

targets = [
    "seq_dense",
    "nlp_dense_1",
    "task_embedding",
    "ihq_embedding",
    "jet_embedding",
    "sibling_context_head",
]

files = list(base.rglob("*.npy"))

print("=== REAL GRECBASE BRANCH WEIGHTS ===")

for target in targets:
    matches = [
        p for p in files
        if target in p.name
    ]
    print(f"\n{target}: {len(matches)} files")

    for p in sorted(matches)[:5]:
        arr = np.load(p, mmap_mode="r")
        print(" ", p.name, tuple(arr.shape))

print("\n=== CURRENT FUSION CONTRACT ===")
print("8 inputs: each (1, 256)")
print("Final output: (1, 10819) — already validated")
print("\nREAD ONLY — NO FILES MODIFIED")
PY
