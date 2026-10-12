podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
sys.path.insert(0, "artifacts/v1.168-max")

from max.dtype import DType
from max.graph import DeviceRef
from cta_max.sequence_postprocess_max import SequencePostprocessMAX

model = SequencePostprocessMAX(
    dtype=DType.float32,
    device=DeviceRef.CPU()
)

print("SEQUENCE POSTPROCESS CONSTRUCTION: PASS")
print("POOLING:", type(model.pooling).__name__)
print("DENSE:", type(model.seq_dense).__name__)
PY
