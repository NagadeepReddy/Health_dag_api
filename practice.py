podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import json
import importlib.util
from pathlib import Path
import torch

root = Path("/workspace/artifacts/v1.168")
pipeline_file = root / "core-artifact/pipeline.py"
sample = root / "samples/sanity_input.json"
output = Path(
    "/workspace/artifacts/v1.168-max/cta_max/"
    "real_sanity_model_in.pt"
)

assert pipeline_file.is_file()
assert sample.is_file()

for path in (
    root,
    root / "core-artifact",
    root / "utils",
    root / "utils/dependency-utils",
):
    sys.path.insert(0, str(path))

spec = importlib.util.spec_from_file_location(
    "original_cta_pipeline", pipeline_file
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

print("ORIGINAL PIPELINE IMPORT: PASS", flush=True)

pipeline = module.pipeline()

print("LOADING ORIGINAL PIPELINE...", flush=True)
pipeline.load()
print("ORIGINAL PIPELINE LOAD: PASS", flush=True)

body = json.loads(sample.read_text())

result = pipeline.preprocess(body)

assert isinstance(result, (tuple, list))
assert len(result) == 6, (
    "Unexpected original preprocessing return contract",
    len(result)
)

model_in, can_in, can_list, context, context_fmt, task_in = result

assert isinstance(model_in, dict)
assert model_in, "Original preprocessing returned empty model input"

print("\nREAL PREPROCESSING: PASS")
print("MODEL INPUT FIELDS:", len(model_in))

def describe(value):
    if hasattr(value, "shape"):
        return f"shape={tuple(value.shape)}, dtype={value.dtype}"
    if isinstance(value, (list, tuple)):
        shapes = [
            tuple(v.shape) if hasattr(v, "shape") else type(v).__name__
            for v in value[:4]
        ]
        return f"{type(value).__name__}, length={len(value)}, samples={shapes}"
    return type(value).__name__

for name, value in model_in.items():
    print(f"{name}: {describe(value)}")

# Keep the actual input on the company machine for
# subsequent MAX inference; do not alter DS source.
torch.save(model_in, output)

print("\nREAL MODEL INPUT SAVED:", output)
print("ORIGINAL PYTORCH AND DS SOURCE UNCHANGED")
PY
