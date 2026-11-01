REPO=/application1/sajjna8/rt-pzai-bplan-v1
OUT="$REPO/artifacts/v1.113-max/maxserve_bplan_extension"

cat > "$OUT/bplan_max_projection_parity.py" <<'PY'
import numpy as np
from pathlib import Path
from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops

p = Path("/bplan_out")

x = np.load(p / "bplan_transfer_input.npy").astype(np.float32)
w = np.load(p / "bplan_transfer_weight.npy").astype(np.float32)
ref = np.load(p / "bplan_transfer_reference.npy").astype(np.float32)

assert x.shape == (1, 2048)
assert w.shape == (10438, 2048)
assert ref.shape == (1, 10438)

weight_t = np.ascontiguousarray(w.T)

device = CPU()
device_ref = DeviceRef.from_device(device)

with Graph(
    "bplan_max_projection",
    input_types=[
        TensorType(DType.float32, [1, 2048], device_ref),
        TensorType(DType.float32, [2048, 10438], device_ref),
    ],
) as graph:
    graph.output(ops.matmul(graph.inputs[0], graph.inputs[1]))

print("MAX GRAPH BUILD: PASS", flush=True)

session = InferenceSession(devices=[device])
model = session.load(graph)

print("MAX GRAPH COMPILE: PASS", flush=True)

result = model.execute(x, weight_t)[0]
actual = result.to_numpy()

assert actual.shape == ref.shape

diff = np.abs(actual - ref)
max_diff = float(diff.max())

print("MAX OUTPUT:", actual.shape)
print("MAX DIFFERENCE:", max_diff)

if not np.allclose(actual, ref, rtol=1e-4, atol=1e-3):
    raise AssertionError("MAX projection parity failed")

np.save(p / "bplan_max_projection_output.npy", actual)
print("BPLAN REAL MAX PROJECTION PARITY: PASS")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$OUT:/bplan_out:rw" \
  -w /bplan_out \
  localhost/cta-max-faiss:local \
  /bplan_out/bplan_max_projection_parity.py
