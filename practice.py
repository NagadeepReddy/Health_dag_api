cat > artifacts/v1.168-max/cta_max/parallel_transformer_block.py <<'PY'
from __future__ import annotations

from max.dtype import DType
from max.graph import DeviceRef, TensorValue
from max.nn import Linear, RMSNorm
from max.nn.layer import Module


class ParallelTransformerBlockMAX(Module):
    """MAX-native CTA ParallelTransformerBlock — sequence_transformer block 0."""

    def __init__(self, dtype: DType, device: DeviceRef) -> None:
        super().__init__()

        # Exact CTA block dimensions:
        # dim=256, dim_head=256, heads=2, ff_mult=4
        self.norm1 = RMSNorm(256, dtype, name="sequence_transformer.ptransformer.0.norm1")
        self.norm2 = RMSNorm(2048, dtype, name="sequence_transformer.ptransformer.0.norm2")

        # PyTorch checkpoint: (3072, 256)
        self.fused_attn_ff_proj = Linear(
            256, 3072, dtype, device,
            has_bias=False,
            name="sequence_transformer.ptransformer.0.fused_attn_ff_proj",
        )

        # PyTorch checkpoint: (256, 512)
        self.attn_out = Linear(
            512, 256, dtype, device,
            has_bias=False,
            name="sequence_transformer.ptransformer.0.attn_out",
        )

        # PyTorch checkpoint: (256, 1024)
        self.ff_out = Linear(
            1024, 256, dtype, device,
            has_bias=False,
            name="sequence_transformer.ptransformer.0.ff_out.1",
        )
PY

echo "MAX TRANSFORMER BLOCK SKELETON CREATED"
