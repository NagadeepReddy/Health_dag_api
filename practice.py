podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
import sys

base = Path("artifacts/v1.168-max/cta_max")
src = base / "parallel_transformer_block_2layers.py"
dst = base / "att_pooling_max.py"
weights = base / "grecbase_integration_weights"

assert src.is_file(), "STOP: verified transformer source missing"
assert not dst.exists(), "STOP: attention adapter already exists"

for name in ("norm1.g", "norm2.g"):
    assert (weights / f"att_pooling.{name}.npy").is_file(), \
        f"STOP: missing att_pooling.{name}"

source = src.read_text()
tree = ast.parse(source)

classes = [
    n for n in tree.body
    if isinstance(n, ast.ClassDef)
    and n.name == "ParallelTransformerBlockMAX"
]
assert len(classes) == 1, "STOP: transformer class differs"

cls = classes[0]

init = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "__init__"
)
forward = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "__call__"
)

assignments = {}

for node in init.body:
    if not isinstance(node, ast.Assign):
        continue
    if len(node.targets) != 1:
        continue
    target = node.targets[0]
    if isinstance(target, ast.Attribute):
        if isinstance(target.value, ast.Name) and target.value.id == "self":
            assignments[target.attr] = node

assert ast.literal_eval(assignments["heads"].value) == 2
assert tuple(ast.literal_eval(
    assignments["fused_dims"].value
)) == (512, 256, 256, 2048)

assignments["heads"].value = ast.Constant(value=1)
assignments["fused_dims"].value = ast.parse(
    "(256, 256, 256, 2048)", mode="eval"
).body

dimensions = {
    "fused_attn_ff_proj": (3072, 2816, 1),
    "attn_out": (512, 256, 0),
}

for name, (old, new, index) in dimensions.items():
    call = assignments[name].value
    assert isinstance(call, ast.Call)
    assert isinstance(call.func, ast.Name) and call.func.id == "Linear"

    if len(call.args) > index:
        assert isinstance(call.args[index], ast.Constant)
        assert call.args[index].value == old, \
            f"STOP: unexpected {name} dimensions"
        call.args[index] = ast.Constant(value=new)
    else:
        keyword = "out_dim" if index == 1 else "in_dim"
        matches = [k for k in call.keywords if k.arg == keyword]
        assert len(matches) == 1 and ast.literal_eval(matches[0].value) == old
        matches[0].value = ast.Constant(value=new)

for name in ("fused_attn_ff_proj", "attn_out", "ff_out"):
    call = assignments[name].value
    keys = [k for k in call.keywords if k.arg == "name"]
    assert len(keys) == 1, f"STOP: missing layer name: {name}"
    keys[0].value = ast.Constant(value=f"att_pooling.{name}" if name != "ff_out"
                                  else "att_pooling.ff_out.1")

loads = sorted([
    n for n in ast.walk(forward)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and isinstance(n.func.value, ast.Name)
    and n.func.value.id == "np"
    and n.func.attr == "load"
], key=lambda n: n.lineno)

assert len(loads) == 2, \
    f"STOP: expected two normalization loads, found {len(loads)}"

for call, name in zip(loads, ("norm1", "norm2")):
    original = ast.get_source_segment(source, call)
    assert f"fn_{name}_g" in original, \
        f"STOP: normalization load order differs: {name}"
    call.args = [
        ast.Constant(
            value=str(weights / f"att_pooling.{name}.g.npy")
        )
    ]
    call.keywords = []

# Preserve the existing forward implementation, including rotary attention.
cls.name = "AttPoolingBlockMAX"

ast.fix_missing_locations(tree)
new_code = ast.unparse(tree) + "\n"
ast.parse(new_code)

# Confirm the adapted class constructs before saving it.
sys.path.insert(0, str(base))
namespace = {}
exec(compile(new_code, str(dst), "exec"), namespace)

from max.dtype import DType
from max.graph import DeviceRef

model = namespace["AttPoolingBlockMAX"](
    dtype=DType.float32,
    device=DeviceRef.CPU(),
    layer_idx=0,
)

assert model.heads == 1
assert tuple(model.fused_dims) == (256, 256, 256, 2048)

dst.write_text(new_code)

print("ONE-HEAD ATTENTION ADAPTER CREATED")
print("CONSTRUCTION: PASS")
print("HEADS:", model.heads)
print("FUSED DIMENSIONS:", model.fused_dims)
print("ORIGINAL TRANSFORMER AND DS CODE UNCHANGED")
PY
