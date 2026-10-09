cat > artifacts/v1.168-max/cta_max/context_head_full.py <<'PY'
from __future__ import annotations

from max.dtype import DType
from max.graph import DeviceRef, TensorValue
from max.nn.layer import Module

from cta_max.context_head_deep import ContextHeadDeepMAX
from cta_max.context_head_wide import ContextHeadWideMAX
from cta_max.context_head_combined import ContextHeadCombinedMAX


class ContextHeadFullMAX(Module):
    """Integrated MAX-native CTA ContextHead."""

    def __init__(self, dtype: DType, device: DeviceRef) -> None:
        super().__init__()

        self.deep = ContextHeadDeepMAX(dtype, device)
        self.wide = ContextHeadWideMAX(dtype, device)
        self.combine = ContextHeadCombinedMAX()

    def __call__(
        self,
        deep_in: list[TensorValue],
        wide_in: TensorValue,
        bn_weight: TensorValue,
        bn_bias: TensorValue,
        running_mean: TensorValue,
        running_var: TensorValue,
    ) -> TensorValue:

        deep_out = self.deep(deep_in)

        wide_out = self.wide(
            wide_in,
            bn_weight,
            bn_bias,
            running_mean,
            running_var,
        )

        return self.combine(deep_out, wide_out)
PY

echo "FULL CONTEXTHEAD INTEGRATED"
