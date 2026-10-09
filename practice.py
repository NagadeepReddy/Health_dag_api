cat > artifacts/v1.168-max/cta_max/context_head_combined.py <<'PY'
from __future__ import annotations

from max.graph import TensorValue, ops
from max.nn.layer import Module


class ContextHeadCombinedMAX(Module):
    """Combine the already validated ContextHead deep and wide outputs."""

    def __call__(
        self,
        deep_out: TensorValue,
        wide_out: TensorValue,
    ) -> TensorValue:
        # Both validated independently as [batch, 128].
        # Original ContextHead combines wide + deep features here.
        return ops.concat([wide_out, deep_out], axis=1)
PY

echo "CONTEXTHEAD COMBINE COMPONENT CREATED"
