python3 -B - <<'PY'
from pathlib import Path
import hashlib

old = Path("/application1/cta_max_true_batch_dev_20261028/cta_max")
repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")

folders = [
    "context_head_weights",
    "get_path_weights",
    "grecbase_aux_weights",
    "grecbase_integration_weights",
    "main_context_weights",
    "nlp_weights",
    "sequence_weights",
    "sibling_context_weights",
]

def inventory(root):
    result = {}
    for p in root.rglob("*.npy"):
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
                h.update(chunk)
        result[p.relative_to(root).as_posix()] = h.hexdigest()
    return result

print("=== MAX WEIGHT COMPARISON ===")
for name in folders:
    a, b = old / name, repo / name
    if not a.is_dir() or not b.is_dir():
        print("MISSING:", name)
        continue
    left, right = inventory(a), inventory(b)
    print(name, "PASS" if left == right else "DIFFERENT",
          "| Old:", len(left), "| Repo:", len(right))
    if left != right:
        for file in sorted(set(left) | set(right)):
            if left.get(file) != right.get(file):
                print("  MISMATCH:", file)

print("READ-ONLY CHECK COMPLETE")
PY
