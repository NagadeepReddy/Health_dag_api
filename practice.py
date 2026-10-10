cat > artifacts/v1.168-max/cta_max/test_transformer_downstream_max.py <<'PY'
import numpy as np

from max.driver import CPU, Tensor
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, Shape, ops
from max.graph.weights import WeightData
from max.nn import Linear

B = "artifacts/v1.168-max/cta_max"
W = B + "/sequence_weights"

device = CPU()
dr = DeviceRef.from_device(device)

x = np.load(B + "/transformer_input.npy").astype(np.float32)
att = np.load(B + "/transformer_attention_pytorch.npy").astype(np.float32)
ff = np.load(B + "/transformer_ff_pytorch.npy").astype(np.float32)

wa = np.load(W + "/fn_attn_out_weight.npy").astype(np.float32)
wf = np.load(W + "/fn_ff_out_1_weight.npy").astype(np.float32)
ng = np.load(W + "/fn_norm2_g.npy").astype(np.float32)

# PyTorch attention output: B,H,S,D -> B,S,H*D
att = att.transpose(0, 2, 1, 3).reshape(1, 4, 512)

weights = {
    "attn_out.weight": WeightData(
        wa, name="attn_out.weight",
        dtype=DType.float32, shape=Shape(wa.shape)
    ),
    "ff_out.weight": WeightData(
        wf, name="ff_out.weight",
        dtype=DType.float32, shape=Shape(wf.shape)
    ),
}

with Graph(
    "transformer_downstream",
    input_types=[
        TensorType(DType.float32, list(x.shape), device=dr),
        TensorType(DType.float32, list(att.shape), device=dr),
        TensorType(DType.float32, list(ff.shape), device=dr),
    ],
) as graph:

    xv, av, fv = graph.inputs

    attn_linear = Linear(
        512, 256, DType.float32, dr,
        has_bias=False, name="attn_out"
    )
    att_out = attn_linear(av)

    # Exact CTA RMSNorm for 2048-dimensional FF tensor.
    gamma = ops.constant(ng, device=dr)
    rms = ops.rsqrt(ops.mean(fv * fv, axis=-1) + 1.0e-6)
    rms = ops.unsqueeze(rms, -1)
    fn = fv * rms * gamma

    # SwiGLU: silu(first half) * second half.
    a = fn[..., :1024]
    b = fn[..., 1024:]
    swiglu = ops.silu(a) * b

    ff_linear = Linear(
        1024, 256, DType.float32, dr,
        has_bias=False, name="ff_out"
    )
    ff_out = ff_linear(swiglu)

    final = xv + att_out + ff_out

    graph.output(att_out, ff_out, final)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

out = model.execute(
    Tensor.from_numpy(x),
    Tensor.from_numpy(att),
    Tensor.from_numpy(ff),
)

max_att = out[0].to_numpy()
max_ff = out[1].to_numpy()
max_final = out[2].to_numpy()

pt_att = np.load(B + "/transformer_attn_projected_pytorch.npy")
pt_ff = np.load(B + "/transformer_ff_out_pytorch.npy")
pt_final = np.load(B + "/transformer_block0_combined_pytorch.npy")

print("ATTN DIFF :", np.max(np.abs(pt_att-max_att)))
print("ATTN MATCH:", np.allclose(pt_att,max_att,rtol=1e-4,atol=1e-5))

print("FF DIFF   :", np.max(np.abs(pt_ff-max_ff)))
print("FF MATCH  :", np.allclose(pt_ff,max_ff,rtol=1e-4,atol=1e-5))

print("FINAL DIFF:", np.max(np.abs(pt_final-max_final)))
print("FINAL MATCH:", np.allclose(pt_final,max_final,rtol=1e-4,atol=1e-5))
PY

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_downstream_max.py && \
echo "DOWNSTREAM MAX TEST CREATED - SYNTAX CLEAN"
