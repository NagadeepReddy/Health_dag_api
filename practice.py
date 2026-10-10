cat > artifacts/v1.168-max/cta_max/test_transformer_rotary_max.py <<'PY'
import numpy as np

from max.driver import CPU, Tensor
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops

BASE = "artifacts/v1.168-max/cta_max"

device = CPU()
device_ref = DeviceRef.from_device(device)

fused = np.load(BASE + "/transformer_fused_pytorch.npy").astype(np.float32)
inv = np.load(BASE + "/sequence_weights/fn_rotary_emb_inv_freq.npy").astype(np.float32)

q = fused[..., :512].reshape(1, 4, 2, 256).transpose(0, 2, 1, 3)
k = fused[..., 512:768].reshape(1, 4, 1, 256).transpose(0, 2, 1, 3)

seq = np.arange(q.shape[2], dtype=np.float32)
freqs = np.einsum("i,j->ij", seq, inv)
pos = np.concatenate((freqs, freqs), axis=-1)[None, None, :, :].astype(np.float32)

with Graph(
    "transformer_rotary_test",
    input_types=[
        TensorType(DType.float32, list(q.shape), device=device_ref),
        TensorType(DType.float32, list(k.shape), device=device_ref),
        TensorType(DType.float32, list(pos.shape), device=device_ref),
    ],
) as graph:
    qv, kv, pv = graph.inputs

    def rotary(x):
        x1 = x[..., :128]
        x2 = x[..., 128:]
        rotated = ops.concat([-x2, x1], axis=-1)
        return x * ops.cos(pv) + rotated * ops.sin(pv)

    qr = rotary(qv)
    kr = rotary(kv)
    graph.output(qr, kr)

session = InferenceSession(devices=[device])
model = session.load(graph)

outputs = model.execute(
    Tensor.from_numpy(q),
    Tensor.from_numpy(k),
    Tensor.from_numpy(pos),
)

def to_np(t):
    if hasattr(t, "to_numpy"):
        return t.to_numpy()
    if hasattr(t, "numpy"):
        return t.numpy()
    return np.asarray(t)

max_q = to_np(outputs[0])
max_k = to_np(outputs[1])

pt_q = np.load(BASE + "/transformer_q_rotary_pytorch.npy")
pt_k = np.load(BASE + "/transformer_k_rotary_pytorch.npy")

print("Q MAX DIFF:", np.max(np.abs(pt_q - max_q)))
print("Q MATCH   :", np.allclose(pt_q, max_q, rtol=1e-4, atol=1e-5))
print("K MAX DIFF:", np.max(np.abs(pt_k - max_k)))
print("K MATCH   :", np.allclose(pt_k, max_k, rtol=1e-4, atol=1e-5))
PY

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_rotary_max.py && echo "ROTARY MAX TEST CREATED - SYNTAX CLEAN"
