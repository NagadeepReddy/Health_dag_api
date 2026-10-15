podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, runpy, io, contextlib
from pathlib import Path
import numpy as np

base = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [str(base), str(base.parent)]

with contextlib.redirect_stdout(io.StringIO()):
    env = runpy.run_path(
        str(base / "run_real_sanity_max_branch_diag.py"),
        run_name="__main__"
    )

outputs = env["outputs"]
assert len(outputs) == 9

final = np.asarray(outputs[0].to_numpy(), dtype=np.float32)
assert final.shape == (1, 2048)

branches = [
    np.asarray(o.to_numpy(), dtype=np.float32).reshape(1, 256)
    for o in outputs[1:]
]

x = np.stack(branches, axis=1)
assert x.shape == (1, 8, 256)

files = sorted(
    set(base.rglob("moe_norm2.g.npy")) |
    set(base.rglob("moe_norm2_g.npy"))
)

print("NORMALIZATION WEIGHT FILES:",
      [str(f.relative_to(base)) for f in files])

if len(files) != 1:
    raise SystemExit("STOP: Need exactly one final normalization weight file")

g = np.load(files[0]).astype(np.float32)
assert g.shape == (256,), g.shape

variance = np.mean(x * x, axis=-1, keepdims=True)
normalized = x * (1.0 / np.sqrt(variance + 1e-6)) * g
candidate = normalized.reshape(1, 2048)

d = np.abs(
    candidate.astype(np.float64) -
    final.astype(np.float64)
)

print("\n=== LEARNED FINAL NORMALIZATION CHECK ===")
print("FINAL SHAPE:", final.shape)
print("RECONSTRUCTED SHAPE:", candidate.shape)
print("MAX_DIFF:", float(d.max()))
print("MEAN_DIFF:", float(d.mean()))
print("MATCH:", bool(np.allclose(
    candidate, final, rtol=1e-3, atol=1e-3
)))
PY
