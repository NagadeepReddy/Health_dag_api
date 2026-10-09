cat > artifacts/v1.168-max/cta_max/context_head_wide.py <<'PY'
from __future__ import annotations

from max.dtype import DType
from max.graph import DeviceRef, TensorValue, ops
from max.nn import Linear
from max.nn.layer import Module


class ContextHeadWideMAX(Module):
    """MAX-native CTA ContextHead wide path."""

    def __init__(self, dtype: DType, device: DeviceRef) -> None:
        super().__init__()

        self.wide_dense = Linear(
            in_dim=127,
            out_dim=128,
            dtype=dtype,
            device=device,
            has_bias=True,
            name="context_head.wide_dense",
        )

        self.swiglu_w1 = Linear(
            128, 86, dtype, device,
            has_bias=False,
            name="context_head.wide_swiglu.w1",
        )
        self.swiglu_w3 = Linear(
            128, 86, dtype, device,
            has_bias=False,
            name="context_head.wide_swiglu.w3",
        )
        self.swiglu_w2 = Linear(
            86, 128, dtype, device,
            has_bias=False,
            name="context_head.wide_swiglu.w2",
        )

    def __call__(
        self,
        wide_in: TensorValue,
        bn_weight: TensorValue,
        bn_bias: TensorValue,
        running_mean: TensorValue,
        running_var: TensorValue,
    ) -> TensorValue:

        # PyTorch BatchNorm1d inference:
        # (x - mean) / sqrt(var + eps) * weight + bias
        x = (wide_in - running_mean) / ops.sqrt(running_var + 1e-5)
        x = x * bn_weight + bn_bias

        x = self.wide_dense(x)

        # Original source: LeakyReLU(0.2)
        x = ops.relu(x) - (ops.relu(-x) * 0.2)

        # Original FFSwiGLU: w2(silu(w1(x)) * w3(x))
        x = self.swiglu_w2(
            ops.silu(self.swiglu_w1(x)) * self.swiglu_w3(x)
        )

        return x
PY
