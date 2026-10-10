cat > artifacts/v1.168-max/cta_max/test_transformer_attention_max.py <<'PY'
import numpy as np

from max.driver import CPU, Tensor
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops

BASE = "artifacts/v1.168-max/cta_max"

device = CPU()
device_ref = DeviceRef.from_device(device)

q = np.load(BASE + "/transformer_q_rotary_pytorch.npy").astype(np.float32)
k = np.load(BASE + "/transformer_k_rotary_pytorch.npy").astype(np.float32)
v = np.load(BASE + "/transformer_v_pytorch.npy").astype(np.float32)

with Graph(
    "transformer_attention_test",
    input_types=[
        TensorType(DType.float32, list(q.shape), device=device_ref),
        TensorType(DType.float32, list(k.shape), device=device_ref),
        TensorType(DType.float32, list(v.shape), device=device_ref),
    ],
) as graph:
    qv, kv, vv = graph.inputs

    # Original CTA block scale: dim_head ** -0.5, dim_head=256
    q_scaled = qv * (256.0 ** -0.5)

    # (B,H,S,D) x (B,H,D,S) -> (B,H,S,S)
    scores = q_scaled @ ops.permute(kv, [0, 1, 3, 2])

    # Sequence length here is 4. Original block uses upper-triangular
    # causal mask, excluding future positions.
    mask = np.triu(
        np.ones((1, 1, 4, 4), dtype=np.float32),
        k=1,
    ) * -1.0e9

    mask_t = ops.constant(mask, device=device_ref)
    scores = scores + mask_t

    probs = ops.softmax(scores, axis=-1)

    # (B,H,S,S) x (B,H,S,D) -> (B,H,S,D)
    out = probs @ vv

    graph.output(probs, out)

session = InferenceSession(devices=[device])
model = session.load(graph)

outputs = model.execute(
    Tensor.from_numpy(q),
    Tensor.from_numpy(k),
    Tensor.from_numpy(v),
)

max_probs = np.asarray(outputs[0])
max_out = np.asarray(outputs[1])

pt_probs = np.load(BASE + "/transformer_attention_probs_pytorch.npy")
pt_out = np.load(BASE + "/transformer_attention_pytorch.npy")

print("PROBS SHAPE:", max_probs.shape)
print("PROBS DIFF :", np.max(np.abs(pt_probs - max_probs)))
print("PROBS MATCH:", np.allclose(pt_probs, max_probs, rtol=1e-4, atol=1e-5))

print("OUT SHAPE  :", max_out.shape)
print("OUT DIFF   :", np.max(np.abs(pt_out - max_out)))
print("OUT MATCH  :", np.allclose(pt_out, max_out, rtol=1e-4, atol=1e-5))
PY

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_attention_max.py && echo "ATTENTION MAX TEST CREATED - SYNTAX CLEAN"
