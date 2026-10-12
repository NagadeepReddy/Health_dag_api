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
    "/workspace/artifacts/v1.168-max/cta_max/real_sanity_model_in.pt"
)

# Import-only guard: no FAISS computations or simulated results.
try:
    import faiss
except ImportError:
    guard = types.ModuleType("faiss")
    guard.__file__ = "<faiss-import-only-guard>"
    guard.__spec__ = importlib.machinery.ModuleSpec("faiss", loader=None)
    def unavailable(name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise RuntimeError("Native FAISS required: " + name)
    guard.__getattr__ = unavailable
    sys.modules["faiss"] = guard

body = copy.deepcopy(json.loads(sample.read_text()))
fixes = []

def adjust(obj, path="$"):
    if isinstance(obj, dict):
        page = obj.get("page")
        if (
            isinstance(page, dict)
            and str(page.get("name", "")).lower() == "gridwall_smartphones"
            and obj.get("webinteraction_name") is None
        ):
            obj["webinteraction_name"] = ""
            fixes.append(path + ".webinteraction_name")
        for k, v in obj.items():
            adjust(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            adjust(v, f"{path}[{i}]")

adjust(body)
print("TEST-ONLY INPUT ADJUSTMENTS:", len(fixes), flush=True)
assert len(fixes) == 6, f"Unexpected adjustments: {fixes}"

for p in (
    root,
    root / "core-artifact",
    root / "utils",
    root / "utils/dependency-utils",
):
    sys.path.insert(0, str(p))

spec = importlib.util.spec_from_file_location(
    "original_cta_pipeline", root / "core-artifact/pipeline.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

pipeline = module.pipeline()
pipeline.load()
print("ORIGINAL PIPELINE LOAD: PASS", flush=True)

result = pipeline.preprocess(body)
assert isinstance(result, (tuple, list))
assert len(result) == 7, f"Unexpected return count: {len(result)}"

(
    model_in, can_in, can_list,
    request_context, request_context_fmt,
    task_in, prod_nm
) = result

print("REAL PREPROCESSING: PASS")
assert isinstance(model_in, dict)
assert len(model_in) == 17, len(model_in)

print("MODEL INPUT FIELDS:", len(model_in))

for name, value in model_in.items():
    if hasattr(value, "shape"):
        print(name, tuple(value.shape), str(value.dtype))
    elif isinstance(value, (list, tuple)):
        shapes = [
            tuple(x.shape) if hasattr(x, "shape")
            else type(x).__name__
            for x in value[:4]
        ]
        print(name, "length:", len(value), "shapes:", shapes)
    else:
        print(name, type(value).__name__)

torch.save(model_in, output)
assert output.is_file() and output.stat().st_size > 0

print("REAL MODEL INPUT SAVED: PASS")
print("PATH:", output)
print("ORIGINAL JSON AND DS SOURCE UNCHANGED")
PY
