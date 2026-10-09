python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

start=s.index("    def __call__(self, x: TensorValue):")

new='''    def __call__(
        self,
        x: TensorValue,
        pos_emb: TensorValue,
    ) -> TensorValue:
        # CTA: norm -> fused Q/K/V/FF projection
        x_norm = self.norm1(x)
        q, k, v, ff = self.fused_attn_ff_proj(x_norm).split(
            [512, 256, 256, 2048],
            axis=-1,
        )

        # Verified CTA dimensions:
        # Q = 2 heads x 256
        # K/V = 1 head x 256 (broadcast over Q heads)
        q = q.reshape([q.shape[0], q.shape[1], 2, 256]).permute([0, 2, 1, 3])
        k = k.reshape([k.shape[0], k.shape[1], 1, 256]).permute([0, 2, 1, 3])
        v = v.reshape([v.shape[0], v.shape[1], 1, 256]).permute([0, 2, 1, 3])

        # CTA rotary position embedding.
        q = apply_rotary_pos_emb_max(pos_emb, q)
        k = apply_rotary_pos_emb_max(pos_emb, k)

        # Scaled dot-product attention.
        q = q * self.scale
        scores = ops.matmul(q, k.transpose(-1, -2))

        # Softmax attention. Padding mask will be supplied by the
        # sequence-level wrapper where valid_length is available.
        attn = ops.softmax(scores, axis=-1)
        out = ops.matmul(attn, v)

        # [B, H, N, D] -> [B, N, H*D]
        out = out.permute([0, 2, 1, 3])
        out = out.reshape([out.shape[0], out.shape[1], 512])
        attn_out = self.attn_out(out)

        # Exact CTA SwiGLU:
        # ff is 2048 = two 1024 branches.
        ff1 = ff[..., :1024]
        ff3 = ff[..., 1024:]
        swiglu = ops.silu(ff1) * ff3
        ff_out = self.ff_out(swiglu)

        # CTA parallel attention + feed-forward output.
        return attn_out + ff_out
'''

s=s[:start]+new+"\n"

with open(p,"w") as f:
    f.write(s)

print("MAX TRANSFORMER ATTENTION AND FF IMPLEMENTED")
PY
