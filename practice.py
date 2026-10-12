podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import json
import types
import importlib.util
from pathlib import Path

root = Path("/workspace/artifacts/v1.168")
sample = root / "samples/sanity_input.json"
output = Path(
    "/workspace/artifacts/v1.168-max/cta_max/real_sanity_model_in.pt"
)

assert sample.is_file()

# Allow import for preprocessing only.
# Any actual FAISS operation must fail explicitly.
try:
    import faiss
    print("NATIVE FAISS AVAILABLE")
except ImportError:
    stub = types.ModuleType("faiss")

    def unavailable(name):
        raise RuntimeError(
            f"Real FAISS operation '{name}' requested. "
            "Native FAISS is required; no simulated results allowed."
        )

    stub.__getattr__ = unavailable
    sys.modules["faiss"] = stub
    print("FAISS IMPORT GUARD ACTIVE — PREPROCESSING ONLY")

import torch

for path in (
    root,
    root / "core-artifact",
    root / "utils",
    root / "utils/dependency-utils",
):
    sys.path.insert(0, str(path))

spec = importlib.util.spec_from_file_location(
    "original_cta_pipeline",
    root / "core-artifact/pipeline.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

print("ORIGINAL PIPELINE IMPORT: PASS", flush=True)

pipeline = module.pipeline()
pipeline.load()

print("ORIGINAL PIPELINE LOAD: PASS", flush=True)

body = json.loads(sample.read_text())
result = pipeline.preprocess(body)

assert isinstance(result, (tuple, list))
assert len(result) == 6, len(result)

model_in = result[0]
assert isinstance(model_in, dict)
assert len(model_in) == 17, len(model_in)

print("REAL PREPROCESSING: PASS")
print("MODEL INPUT FIELDS:", len(model_in))

for name, value in model_in.items():
    if hasattr(value, "shape"):
        print(name, tuple(value.shape), str(value.dtype))
    elif isinstance(value, (list, tuple)):
        print(name, "list length:", len(value))
    else:
        print(name, type(value).__name__)

torch.save(model_in, output)

print("REAL MODEL INPUT SAVED:", output)
print("ORIGINAL PYTORCH AND DS SOURCE UNCHANGED")
PY
