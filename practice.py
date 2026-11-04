cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
import torch
import numpy as np
import hashlib
from pathlib import Path

root = Path("artifacts/v1.472-max/pzaas_max/validation")

print("=== PZAAS EXACT PYTORCH INPUT PROVENANCE ===")

def load(name):
    p = root / name
    if not p.is_file():
        print(name, "NOT FOUND")
        return None
    obj = torch.load(p, map_location="cpu", weights_only=True)
    print(name, "READ")
    return obj

def canonical(x):
    if isinstance(x, torch.Tensor):
        x = x.detach().cpu().numpy()
    if isinstance(x, np.ndarray):
        a = np.ascontiguousarray(x)
        return (
            "array", str(a.dtype), tuple(a.shape),
            hashlib.sha256(a.tobytes()).hexdigest()
        )
    if isinstance(x, dict):
        return (
            "dict",
            tuple(sorted(
                (str(k), canonical(v)) for k, v in x.items()
            ))
        )
    if isinstance(x, (list, tuple)):
        return ("sequence", tuple(canonical(v) for v in x))
    return ("scalar", repr(x))

def as_array(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    if isinstance(x, np.ndarray):
        return x
    return None

saved = load("ppa_model_input_exact.pt")
base = load("ppa_model_base_reference.pt")
other = load("ppa_pytorch_reference_01.pt")

if isinstance(saved, dict) and "model_in" in saved:
    saved_input = saved["model_in"]
else:
    saved_input = saved

references = {}

for label, obj in [("BASE", base), ("PYTORCH", other)]:
    if not isinstance(obj, dict):
        print(label, "REFERENCE STRUCTURE: UNAVAILABLE")
        continue

    print(label, "KEYS:", list(obj.keys())[:30])

    if "model_in" in obj:
        references[label] = obj["model_in"]

        if saved_input is not None:
            same = canonical(saved_input) == canonical(obj["model_in"])
            print(label, "SAVED INPUT MATCH:", same)
        else:
            print(label, "SAVED INPUT MATCH: NOT CHECKED")

    if "output" in obj:
        a = as_array(obj["output"])
        if a is not None:
            print(label, "OUTPUT SHAPE:", a.shape)
            print(label, "OUTPUT FINITE:", bool(np.isfinite(a).all()))

if "BASE" in references and "PYTORCH" in references:
    print(
        "BOTH REFERENCES USE IDENTICAL INPUT:",
        canonical(references["BASE"]) ==
        canonical(references["PYTORCH"])
    )

if isinstance(base, dict) and isinstance(other, dict):
    a = as_array(base.get("output"))
    b = as_array(other.get("output"))

    if a is not None and b is not None and a.shape == b.shape:
        print(
            "TWO PYTORCH OUTPUTS MAX DIFF:",
            float(np.max(np.abs(a.astype(np.float64) -
                                b.astype(np.float64))))
        )

targets = root / "pzaas_eight_branch_targets.npz"
if targets.is_file():
    with np.load(targets, allow_pickle=False) as z:
        names = [
            "sequence", "context", "search0", "search1",
            "jet", "ihq", "sibling", "task"
        ]
        print("BRANCH TARGETS:", len([n for n in names if n in z]))
        print("BRANCH TARGETS: INTERMEDIATE FEATURES")

print("FULL-OUTPUT VS BRANCH-CONCAT: NOT A VALID PARITY TEST")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
PY
