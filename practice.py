python - <<'PY'
from pathlib import Path

src = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_max.py")
dst = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_rotary_test.py")

s = src.read_text()

old = """        q = apply_rotary_pos_emb_max(pos_emb, q)
        k = apply_rotary_pos_emb_max(pos_emb, k)
"""

new = """        q = apply_rotary_pos_emb_max(pos_emb, q)
        k = apply_rotary_pos_emb_max(pos_emb, k)

        # Temporary parity boundary
        return q, k, v
"""

assert old in s, "ROTARY BOUNDARY NOT FOUND - NOTHING CHANGED"

dst.write_text(s.replace(old, new, 1))
print("MAX ROTARY PARITY BLOCK CREATED")
PY
