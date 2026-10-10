python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block.py")
s = p.read_text()

old = """        # Exact CTA SwiGLU.
        # ff is 2048 = two 1024 branches.
        ff1 = ff[..., :1024]"""

new = """        # Apply the original CTA norm2 before SwiGLU.
        ff = ff * ops.rsqrt(
            ops.mean(ff * ff, axis=-1, keepdims=True) + 1e-6
        ) * self.ff_norm2_g

        # Exact CTA SwiGLU.
        # ff is 2048 = two 1024 branches.
        ff1 = ff[..., :1024]"""

assert s.count(old) == 1, "FF insertion point not found uniquely"

# The trained norm2 weight must be explicitly wired into the graph.
# Do not write a partial implementation that would fail at runtime.
if "self.ff_norm2_g =" not in s:
    print("NORM2 NOT PATCHED: weight binding is not yet defined.")
    print("Need to wire the existing norm2 checkpoint weight safely.")
else:
    s = s.replace(old, new, 1)
    compile(s, str(p), "exec")
    p.write_text(s)
    print("NORM2 PATCHED - SYNTAX CLEAN")
PY
