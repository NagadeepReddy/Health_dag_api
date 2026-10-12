podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import json
import subprocess
import importlib.util
from pathlib import Path

root = Path("/workspace/artifacts/v1.168")
output = Path(
    "/workspace/artifacts/v1.168-max/cta_max/"
    "real_sanity_model_in.pt"
)

# Install only the missing runtime package.
# Preserve existing NumPy and other dependencies.
try:
    import faiss
except ImportError:
    print("INSTALLING FAISS IN TEMPORARY CONTAINER...", flush=True)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--disable-pip-version-check",
        "--no-cache-dir", "--no-deps", "faiss-cpu"
    ])
    import faiss

print("FAISS IMPORT: PASS", flush=True)

import torch

for path in (
    root,
    root / "core-artifact",
    root / "utils",
    root / "utils/dependency-utils",
):
    sys.path.insert(0, str(path))

pipeline_file = root / "core-artifact/pipeline.py"
sample = root / "samples/sanity_input.json"

assert pipeline_file.is_file()
assert sample.is_file()

spec = importlib.util.spec_from_file_location(
    "original_cta_pipeline", pipeline_file
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
print("ORIGINAL DS SOURCE UNCHANGED")
PY
