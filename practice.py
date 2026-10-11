python - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("artifacts/v1.168-max/cta_max")
p = base / "parallel_transformer_block.py"
backup = base / "parallel_transformer_block.pre_norm2_verified.bak"
weight = base / "sequence_weights/fn_norm2_g.npy"

s = p.read_text()

old = """        ff1 = ff[..., :1024]
        ff3 = ff[..., 1024:]
        swiglu = ops.silu(ff1) * ff3"""

new = """        import numpy as np
        norm2_g = ops.constant(
            np.load("artifacts/v1.168-max/cta_max/sequence_weights/fn_norm2_g.npy").astype(np.float32),
            dtype=ff.dtype,
            device=DeviceRef.CPU(),
        )
        variance2 = ops.mean(ff * ff, axis=-1)
        ff = ff * ops.rsqrt(variance2 + 1e-6) * norm2_g

        ff1 = ff[..., :1024]
        ff3 = ff[..., 1024:]
        swiglu = ops.silu(ff3) * ff1"""

assert s.count(old) == 1, f"STOP: exact FF block found {s.count(old)} times"
assert weight.is_file(), "STOP: verified norm2 weight missing"
assert not backup.exists(), "STOP: backup already exists"

updated = s.replace(old, new, 1)
ast.parse(updated)

shutil.copy2(p, backup)
p.write_text(updated)

print("REAL MAX FF FIX APPLIED")
print("SYNTAX VERIFIED")
print("ORIGINAL BACKED UP")
PY
