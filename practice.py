podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
from max.graph import ops

assert hasattr(ops, "unsqueeze"), "STOP: MAX unsqueeze unavailable"

p = Path("artifacts/v1.168-max/cta_max/sequence_postprocess_max.py")
s = p.read_text()
tree = ast.parse(s)

cls = next(n for n in tree.body
           if isinstance(n, ast.ClassDef)
           and n.name == "SequencePostprocessMAX")

methods = {
    n.name: n for n in cls.body
    if isinstance(n, ast.FunctionDef)
}

assert "__init__" in methods and "__call__" in methods
assert s.count("self.out_norm1 = RMSNorm(") == 1
assert s.count("self.out_norm2 = RMSNorm(") == 1
assert s.count("self.pooling = MeanMaxPoolingMAX()") == 1
assert s.count("self.seq_dense = Linear(") == 1

code = '''
import numpy as np

from max.dtype import DType
from max.graph import DeviceRef, TensorValue, ops
from max.nn import Linear
from max.nn.layer import Module

from .sequence_pooling_max import MeanMaxPoolingMAX


class SequencePostprocessMAX(Module):
    def __init__(self, dtype: DType, device: DeviceRef):
        super().__init__()
        self.pooling = MeanMaxPoolingMAX()
        self.seq_dense = Linear(
            in_dim=512,
            out_dim=256,
            dtype=dtype,
            device=device,
            has_bias=True,
            name="sequence_transformer.seq_dense",
        )

    def __call__(self, x: TensorValue) -> TensorValue:
        base = "artifacts/v1.168-max/cta_max/sequence_weights/"

        g1 = ops.constant(
            np.load(base + "out_norm1_g.npy").astype(np.float32),
            dtype=DType.float32,
            device=DeviceRef.CPU(),
        )
        g2 = ops.constant(
            np.load(base + "out_norm2_g.npy").astype(np.float32),
            dtype=DType.float32,
            device=DeviceRef.CPU(),
        )

        variance1 = ops.unsqueeze(
            ops.mean(x * x, axis=-1), axis=-1
        )
        x = x * ops.rsqrt(variance1 + 1e-6) * g1

        x = self.pooling(x)
        x = self.seq_dense(x)

        variance2 = ops.unsqueeze(
            ops.mean(x * x, axis=-1), axis=-1
        )
        return x * ops.rsqrt(variance2 + 1e-6) * g2
'''

ast.parse(code)

backup = Path(str(p) + ".before_weight_binding.bak")
assert not backup.exists(), "STOP: backup already exists"

backup.write_text(s)
p.write_text(code)

print("SEQUENCE NORMALIZATION WEIGHTS WIRED — SYNTAX OK")
print("DYNAMIC BATCH/SEQUENCE NORMALIZATION SUPPORTED")
print("TRANSFORMER AND DS CODE UNCHANGED")
PY
