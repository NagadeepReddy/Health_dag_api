cat > artifacts/v1.168-max/cta_max/sequence_transformer_max.py <<'PY'
from __future__ import annotations

from max.dtype import DType
from max.graph import DeviceRef, TensorValue, ops
from max.nn import Embedding, Linear
from max.nn.layer import Module


class ParallelTransformerMAEPMAX(Module):
    """MAX-native CTA ParallelTransformerMAEP."""

    def __init__(self, dtype: DType, device: DeviceRef) -> None:
        super().__init__()

        # Real checkpoint dimensions captured from model_0_base.pt
        self.page_embedding = Embedding(
            vocab_size=15,
            hidden_dim=224,
            dtype=dtype,
            device=device,
            name="sequence_transformer.page_embedding",
        )

        self.item_embedding = Embedding(
            vocab_size=10727,
            hidden_dim=112,
            dtype=dtype,
            device=device,
            name="sequence_transformer.item_embedding",
        )

        self.item_meta_embedding = Embedding(
            vocab_size=523,
            hidden_dim=32,
            dtype=dtype,
            device=device,
            name="sequence_transformer.item_meta_embedding",
        )

        self.item_pre_embedding = Embedding(
            vocab_size=10727,
            hidden_dim=112,
            dtype=dtype,
            device=device,
            name="sequence_transformer.item_pre_embedding",
        )

        self.page_meta_wide_dense = Linear(
            in_dim=1,
            out_dim=32,
            dtype=dtype,
            device=device,
            has_bias=True,
            name="sequence_transformer.page_meta_wide_dense",
        )

        self.seq_dense = Linear(
            in_dim=512,
            out_dim=256,
            dtype=dtype,
            device=device,
            has_bias=True,
            name="sequence_transformer.seq_dense",
        )

    def __call__(
        self,
        page_in: TensorValue,
        item_in: TensorValue,
        item_meta_in: TensorValue,
        item_pre_in: TensorValue,
        page_meta_wide_in: TensorValue,
    ):
        page = self.page_embedding(page_in)
        item = self.item_embedding(item_in)
        item_meta = self.item_meta_embedding(item_meta_in)
        item_pre = self.item_pre_embedding(item_pre_in)
        page_wide = self.page_meta_wide_dense(page_meta_wide_in)

        # Keep components separate here. The original model's exact
        # sequence assembly + ptransformer follows in the next block.
        return page, item, item_meta, item_pre, page_wide
PY

echo "SEQUENCE TRANSFORMER MAX FRONTEND CREATED"
