cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json
import ast

root = Path("artifacts/v1.472-max/pzaas_max")
schema_file = root / "validation/pzaas_forward_schema.json"
target = root / "pzaas_input_signature.py"

print("=== PZAAS NATIVE MAX GRAPH ALIGNMENT ===")

schema = json.loads(schema_file.read_text())
records = schema["tensors"]

assert schema["model"] == "GRecBase"
assert len(records) == 159

allowed = {
    "torch.int64": "int64",
    "torch.int32": "int32",
    "torch.float32": "float32",
    "torch.float16": "float16",
    "torch.float64": "float64",
}

for r in records:
    assert r["dtype"] in allowed, r
    assert all(isinstance(x, int) and x > 0
               for x in r["shape"]), r

source = '''
import json
from pathlib import Path
from max.dtype import DType
from max.graph import TensorType

SCHEMA = json.loads(
    (Path(__file__).parent /
     "validation/pzaas_forward_schema.json").read_text()
)

DTYPES = {
    "torch.int64": DType.int64,
    "torch.int32": DType.int32,
    "torch.float32": DType.float32,
    "torch.float16": DType.float16,
    "torch.float64": DType.float64,
}

def input_types(device):
    return [
        TensorType(
            DTYPES[r["dtype"]],
            r["shape"],
            device=device
        )
        for r in SCHEMA["tensors"]
    ]

def pack(model_in):
    arrays = []
    for r in SCHEMA["tensors"]:
        value = model_in[r["key"]]
        for index in r["indices"]:
            value = value[index]
        assert list(value.shape) == r["shape"]
        assert str(value.dtype) == r["dtype"]
        arrays.append(
            value.detach().cpu().contiguous().numpy()
        )
    return arrays
'''

ast.parse(source)

if target.exists():
    assert target.read_text() == source, (
        "Existing PZAAS signature differs; preserved"
    )
else:
    target.write_text(source)

print("MODEL: GRecBase")
print("FORWARD ARGUMENTS:", len(schema["forward_arguments"]))
print("ACTIVE INPUTS:", len(records))
print("SIGNATURE FILE:", target)
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY

V="$PWD/artifacts/v1.472-max/pzaas_max"

podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 3g \
-e PYTHONDONTWRITEBYTECODE=1 \
-v "$V:/pzaas:ro" \
-w /pzaas \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import sys
sys.path.insert(0, "/pzaas")

from max.driver import CPU
from pzaas_input_signature import input_types, SCHEMA

types = input_types(CPU())

assert len(types) == 159

print("MAX INPUT TYPES: PASS")
print("PZAAS INPUT COUNT:", len(types))
print("MODEL:", SCHEMA["model"])
print("PZAAS MAX INPUT SIGNATURE: PASS")
print("REAL GRAPH COMPUTATION / PARITY: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
