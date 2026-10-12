podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import runpy
import numpy as np

sys.path.insert(0, "artifacts/v1.168-max")
sys.path.insert(0, "artifacts/v1.168-max/cta_max")

from max.dtype import DType
from max.graph import DeviceRef, ops
from cta_max.sequence_postprocess_max import SequencePostprocessMAX

def traced_call(self, x):
    base = "artifacts/v1.168-max/cta_max/sequence_weights/"

    print("INPUT:", x.shape, flush=True)

    g1 = ops.constant(
        np.load(base + "out_norm1_g.npy").astype(np.float32),
        dtype=DType.float32, device=DeviceRef.CPU()
    )
    g2 = ops.constant(
        np.load(base + "out_norm2_g.npy").astype(np.float32),
        dtype=DType.float32, device=DeviceRef.CPU()
    )
    print("G1:", g1.shape, "G2:", g2.shape, flush=True)

    variance1 = ops.unsqueeze(
        ops.mean(x * x, axis=-1), axis=-1
    )
    print("VARIANCE1:", variance1.shape, flush=True)

    x = x * ops.rsqrt(variance1 + 1e-6)
    print("AFTER RMS1:", x.shape, flush=True)

    x = x * g1
    print("AFTER G1:", x.shape, flush=True)

    x = self.pooling(x)
    print("AFTER POOLING:", x.shape, flush=True)

    x = self.seq_dense(x)
    print("AFTER DENSE:", x.shape, flush=True)

    variance2 = ops.unsqueeze(
        ops.mean(x * x, axis=-1), axis=-1
    )
    print("VARIANCE2:", variance2.shape, flush=True)

    x = x * ops.rsqrt(variance2 + 1e-6)
    print("AFTER RMS2:", x.shape, flush=True)

    x = x * g2
    print("AFTER G2:", x.shape, flush=True)

    return x

SequencePostprocessMAX.__call__ = traced_call

runpy.run_path(
    "artifacts/v1.168-max/cta_max/run_transformer_sequence.py",
    run_name="__main__"
)
PY
