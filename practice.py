podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
from max.graph import ops

assert all(hasattr(ops, n) for n in ("mean", "max", "concat")), \
    "STOP: required MAX operation unavailable"

p = Path("artifacts/v1.168-max/cta_max/sequence_pooling_max.py")
assert not p.exists(), "STOP: file already exists"

code = '''
from max.graph import TensorValue, ops
from max.nn.layer import Module

class MeanMaxPoolingMAX(Module):
    def __call__(self, x: TensorValue) -> TensorValue:
        mean_out = ops.mean(x, axis=1)
        max_out = ops.max(x, axis=1)
        return ops.concat([mean_out, max_out], axis=1)
'''

ast.parse(code)
p.write_text(code)

print("MAX MEAN-MAX POOLING CREATED — SYNTAX OK")
print("ORIGINAL MODEL AND VERIFIED TRANSFORMER UNCHANGED")
PY
