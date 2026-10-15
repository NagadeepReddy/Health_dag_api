podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, runpy, io, contextlib
from pathlib import Path
import numpy as np

BASE = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [str(BASE), str(BASE.parent)]
WDIR = BASE / "grecbase_integration_weights"

def weight(name):
    p = WDIR / (name + ".npy")
    if not p.is_file():
        matches = list(BASE.rglob(name + ".npy"))
        if len(matches) != 1:
            print("WEIGHT NOT UNIQUELY FOUND:", name)
            print("CANDIDATES:", [str(x) for x in matches])
            raise SystemExit(1)
        p = matches[0]
    return np.load(p).astype(np.float32)

def norm(x, g):
    variance = np.mean(x * x, axis=-1, keepdims=True)
    return x * np.reciprocal(
        np.sqrt(variance + np.float32(1e-6))
    ) * g

def linear(x, w):
    assert x.shape[-1] == w.shape[1], (x.shape, w.shape)
    return x @ w.T

def rotate_half(x):
    half = x.shape[-1] // 2
    return np.concatenate(
        [-x[..., half:], x[..., :half]], axis=-1
    )

print("Running existing MAX graph...", flush=True)

with contextlib.redirect_stdout(io.StringIO()):
    env = runpy.run_path(
        str(BASE / "run_real_sanity_max_branch_diag.py"),
        run_name="__main__"
    )

outputs = env["outputs"]
assert len(outputs) == 9

actual = np.asarray(
    outputs[0].to_numpy(), dtype=np.float32
)
assert actual.shape == (1, 2048)

parts = [
    np.asarray(o.to_numpy(), dtype=np.float32).reshape(1, 256)
    for o in outputs[1:]
]

x = np.stack(parts, axis=1)
assert x.shape == (1, 8, 256)

# Original graph: moe_norm1
x = norm(x, weight("moe_norm1.g"))

# Attention pooling: first normalization and fused Q/K/V/FF
x_norm = norm(x, weight("att_pooling.norm1.g"))
fused = linear(
    x_norm,
    weight("att_pooling.fused_attn_ff_proj.weight")
)
assert fused.shape == (1, 8, 2816)

q, k, v, ff = np.split(fused, [256, 512, 768], axis=-1)

# Original rotary position embedding
inv = weight("att_pooling.rotary_emb.inv_freq").reshape(-1)
assert inv.size == 128, inv.shape

angles = np.arange(8, dtype=np.float32)[:, None] * inv[None, :]
pos = np.concatenate([angles, angles], axis=-1)[None, :, :]

c = np.cos(pos)
s = np.sin(pos)

q = q * c + rotate_half(q) * s
k = k * c + rotate_half(k) * s

# Attention
q = q * np.float32(256 ** -0.5)
scores = q @ np.swapaxes(k, -1, -2)
scores = scores - scores.max(axis=-1, keepdims=True)
prob = np.exp(scores)
prob = prob / prob.sum(axis=-1, keepdims=True)

attn_out = linear(
    prob @ v,
    weight("att_pooling.attn_out.weight")
)

# Feedforward
ff = norm(ff, weight("att_pooling.norm2.g"))
ff1, ff3 = np.split(ff, 2, axis=-1)
silu = ff3 / (1.0 + np.exp(-ff3))
ff_out = linear(
    silu * ff1,
    weight("att_pooling.ff_out.1.weight")
)

# Original graph: moe_norm2 and reshape
candidate = norm(
    attn_out + ff_out,
    weight("moe_norm2.g")
).reshape(1, 2048)

diff = np.abs(
    candidate.astype(np.float64) -
    actual.astype(np.float64)
)

print("\n=== COMPLETE FINAL ATTENTION-POOLING PARITY ===")
print("MAX SHAPE:", actual.shape)
print("RECONSTRUCTED SHAPE:", candidate.shape)
print("MAX_DIFF:", float(diff.max()))
print("MEAN_DIFF:", float(diff.mean()))
print("MATCH:", bool(np.allclose(
    candidate, actual, rtol=1e-3, atol=1e-3
)))
PY
