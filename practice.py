cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 3g \
-e PYTHONDONTWRITEBYTECODE=1 \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-w /workspace \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import ast, json, os, importlib.util
from pathlib import Path
import torch

os.umask(0o077)
print("=== PZAAS NATIVE MAX INPUT ADAPTER ===")

ref = torch.load(
    "/validation/ppa_pytorch_reference_01.pt",
    map_location="cpu",
    weights_only=True
)
model_in = ref["model_in"]

source = Path(
    "artifacts/v1.472/utils/dependency-utils/models.py"
).read_text()

tree = ast.parse(source)
cls = next(
    n for n in tree.body
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
)
forward = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef) and n.name == "forward"
)

args = [a.arg for a in forward.args.args if a.arg != "self"]
records = []

def flatten(key, value, indices=()):
    if isinstance(value, torch.Tensor):
        records.append({
            "key": key,
            "indices": list(indices),
            "shape": list(value.shape),
            "dtype": str(value.dtype)
        })
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            flatten(key, item, indices + (i,))
    else:
        raise TypeError(f"Unexpected input type: {key}")

for arg in args:
    key = "task_in" if arg == "tasks_in" else arg
    assert key in model_in, f"Missing DS input: {key}"
    flatten(key, model_in[key])

assert len(args) == 16
assert len(records) == 159, (
    f"Unexpected active tensor count: {len(records)}"
)

schema = Path("/validation/pzaas_forward_schema.json")
schema.write_text(json.dumps({
    "model": "GRecBase",
    "forward_arguments": args,
    "tensors": records
}, indent=2))
schema.chmod(0o600)

adapter = Path("/validation/pzaas_forward_input_adapter.py")
adapter.write_text('''
import json
from pathlib import Path
import torch

SCHEMA = json.loads(
    Path(__file__).with_name(
        "pzaas_forward_schema.json"
    ).read_text()
)

def pack(model_in):
    result = []
    for spec in SCHEMA["tensors"]:
        value = model_in[spec["key"]]
        for index in spec["indices"]:
            value = value[index]
        assert isinstance(value, torch.Tensor)
        assert list(value.shape) == spec["shape"]
        assert str(value.dtype) == spec["dtype"]
        result.append(
            value.detach().cpu().contiguous().numpy()
        )
    return result
''')
adapter.chmod(0o600)

spec = importlib.util.spec_from_file_location(
    "pzaas_adapter", adapter
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

packed = module.pack(model_in)
assert len(packed) == len(records)

print("MODEL: GRecBase")
print("FORWARD ARGUMENTS:", len(args))
print("ACTIVE INPUT TENSORS:", len(packed))
print("INPUT SHAPES / DTYPES: VERIFIED")
print("PZAAS INPUT ADAPTER: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("PZAAS MAX GRAPH ALIGNMENT: NEXT")
PY
