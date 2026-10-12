python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
dst = base / "sequence_postprocess_max.py"

assert not dst.exists(), "STOP: file already exists"
assert (base / "sequence_pooling_max.py").is_file()

code = '''
from max.dtype import DType
from max.graph import DeviceRef, TensorValue
from max.nn import Linear, RMSNorm
from max.nn.layer import Module

from .sequence_pooling_max import MeanMaxPoolingMAX


class SequencePostprocessMAX(Module):
    def __init__(self, dtype: DType, device: DeviceRef):
        super().__init__()

        self.out_norm1 = RMSNorm(
            dim=256, dtype=dtype, eps=1e-6
        )
        self.pooling = MeanMaxPoolingMAX()
        self.seq_dense = Linear(
            in_dim=512,
            out_dim=256,
            dtype=dtype,
            device=device,
            has_bias=True,
            name="sequence_transformer.seq_dense",
        )
        self.out_norm2 = RMSNorm(
            dim=256, dtype=dtype, eps=1e-6
        )

    def __call__(self, x: TensorValue) -> TensorValue:
        x = self.out_norm1(x)
        x = self.pooling(x)
        x = self.seq_dense(x)
        return self.out_norm2(x)
'''

ast.parse(code)
dst.write_text(code)

print("SEQUENCE POSTPROCESS COMPONENT CREATED — SYNTAX OK")
print("ORIGINAL TRANSFORMER AND DS CODE UNCHANGED")
PY
