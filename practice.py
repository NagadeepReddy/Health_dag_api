podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, types, importlib.util, importlib.machinery
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.168")
base = Path("/workspace/artifacts/v1.168-max/cta_max")

data = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

deep = data["sibling_deep_in"].numpy()
wide = data["sibling_wide_in"].numpy()

print("=== REAL SIBLING INPUT CHECK ===")
print("DEEP SHAPE:", deep.shape)
print("WIDE SHAPE:", wide.shape)
print("DEEP UNIQUE SIBLINGS:",
      len(np.unique(deep[0].T, axis=0)))
print("WIDE UNIQUE SIBLINGS:",
      len(np.unique(wide[0].T, axis=0)))
print("DEEP FIRST:", deep[0, :, 0].tolist())
print("WIDE FIRST MIN/MAX:",
      int(wide[0, :, 0].min()),
      int(wide[0, :, 0].max()))
print("WIDE NONZERO:", int(np.count_nonzero(wide)))

# Load the same original model that produced the reference.
try:
    import faiss
except ImportError:
    guard = types.ModuleType("faiss")
    guard.__file__ = "<import-only-guard>"
    guard.__spec__ = importlib.machinery.ModuleSpec(
        "faiss", loader=None
    )
    def missing(name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise RuntimeError("Native FAISS required: " + name)
    guard.__getattr__ = missing
    sys.modules["faiss"] = guard

for p in (
    root, root / "core-artifact",
    root / "utils",
    root / "utils/dependency-utils"
):
    sys.path.insert(0, str(p))

spec = importlib.util.spec_from_file_location(
    "cta_pipeline", root / "core-artifact/pipeline.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

pipeline = module.pipeline()
pipeline.load()

state = pipeline.model_base.state_dict()
keys = {
    k: v.detach().cpu().numpy()
    for k, v in state.items()
    if k.startswith("sibling_context_head.")
}

print("\n=== ORIGINAL VS EXPORTED SIBLING WEIGHTS ===")
print("ORIGINAL TENSORS:", len(keys))

matched = 0
different = []
missing = []
ambiguous = []

for name, expected in sorted(keys.items()):
    paths = list(base.rglob(name + ".npy"))

    if len(paths) == 0:
        missing.append(name)
        continue
    if len(paths) != 1:
        ambiguous.append(name)
        continue

    actual = np.load(paths[0])

    if actual.shape != expected.shape:
        different.append((name, "SHAPE MISMATCH"))
        continue

    diff = float(np.max(np.abs(
        actual.astype(np.float64)
        - expected.astype(np.float64)
    )))

    if diff <= 1e-6:
        matched += 1
    else:
        different.append((name, diff))

print("WEIGHTS MATCHED:", matched)
print("WEIGHTS DIFFERENT:", len(different))
print("WEIGHTS MISSING:", len(missing))
print("AMBIGUOUS MATCHES:", len(ambiguous))

for name, detail in different[:10]:
    print("DIFFERENT:", name, detail)
for name in missing[:10]:
    print("MISSING:", name)
for name in ambiguous[:10]:
    print("AMBIGUOUS:", name)

print("\nREAD ONLY — NO SOURCE FILES MODIFIED")
PY
