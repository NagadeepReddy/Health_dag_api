cp artifacts/v1.168-max/cta_max/parallel_transformer_block.py \
   artifacts/v1.168-max/cta_max/parallel_transformer_block.py.pre_mask && \
python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block.py")
s = p.read_text()

old = """scores = ops.matmul(q, k.transpose(-1, -2))

        # Softmax attention. Padding mask will be supplied by the
        # sequence-level wrapper where valid_length is available.
        attn = ops.softmax(scores)"""

new = """scores = ops.matmul(q, k.transpose(-1, -2))

        # CTA causal attention mask: block future positions before softmax.
        n = scores.shape[-1]
        row = ops.constant([[0], [1], [2], [3]], dtype=DType.int64, device=self.device)
        col = ops.constant([[0, 1, 2, 3]], dtype=DType.int64, device=self.device)
        causal = col > row
        neg_inf = ops.constant(-1.0e9, dtype=DType.float32, device=self.device)
        scores = ops.where(causal, neg_inf, scores)

        attn = ops.softmax(scores)"""

if old not in s:
    raise SystemExit("ATTENTION BLOCK NOT FOUND - NOTHING CHANGED")

p.write_text(s.replace(old, new, 1))
print("CAUSAL MASK PATCHED")
PY
