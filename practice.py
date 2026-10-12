podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, json, copy, types
import importlib.util, importlib.machinery
from pathlib import Path
import torch

root = Path("/workspace/artifacts/v1.168")
sample = root / "samples/sanity_input.json"
output = Path(
    "/workspace/artifacts/v1.168-max/cta_max/"
    "real_sanity_model_in.pt"
)

assert sample.is_file()

# Import-only FAISS guard: never simulate FAISS calculations.
try:
    import faiss
    print("FAISS: NATIVE")
except ImportError:
    guard = types.ModuleType("faiss")
    guard.__file__ = "<faiss-import-guard>"
    guard.__spec__ = importlib.machinery.ModuleSpec(
        "faiss", loader=None
    )
    def unavailable(name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise RuntimeError(
            f"Real FAISS operation '{name}' requires native FAISS"
        )
    guard.__getattr__ = unavailable
    sys.modules["faiss"] = guard
    print("FAISS: IMPORT-ONLY GUARD")

# Preserve original JSON; adjust only an in-memory test copy.
original = json.loads(sample.read_text())
body = copy.deepcopy(original)
fixes = []

def normalize(value, path="$"):
    if isinstance(value, dict):
        page = value.get("page")
        if (
            isinstance(page, dict)
            and str(page.get("name", "")).lower()
                == "gridwall_smartphones"
            and value.get("webinteraction_name") is None
        ):
            value["webinteraction_name"] = ""
            fixes.append(path + ".webinteraction_name")

        for key, child in value.items():
            normalize(child, path + "." + str(key))

    elif isinstance(value, list):
        for i, child in enumerate(value):
            normalize(child, f"{path}[{i}]")

normalize(body)

print("TEST-ONLY NULL ADJUSTMENTS:", len(fixes))
for path in fixes[:5]:
    print(" ", path, "None -> empty string")

if not fixes:
    print("Expected invalid field not located.")
    print("No files changed.")
    raise SystemExit(1)

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

pipeline = module.pipeline()
pipeline.load()

print("ORIGINAL PIPELINE LOAD: PASS", flush=True)

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

print("MODEL INPUT SAVED:", output)
print("TEST INPUT ADJUSTED IN MEMORY ONLY")
print("ORIGINAL JSON AND DS SOURCE UNCHANGED")
PY
