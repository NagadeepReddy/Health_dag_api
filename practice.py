podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import re
import textwrap

runner = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py")
source = runner.read_text()

match = re.search(r"(?m)^([ \t]*)branches\s*=", source)
if not match:
    raise SystemExit("STOP: runner insertion point not found")

diagnostic = '''
import sys as _sys
import numpy as _np
import torch as _torch

_sys.path.insert(0, "artifacts/v1.168/utils/dependency-utils")
from models import RMSNorm as _RMSNorm

_p = Path("artifacts/v1.168-max/cta_max")

with _np.load(_p / "max_sequence_stages_diag.npz") as _data:
    _x = _torch.from_numpy(_data["after_block1"].copy())

_state = _torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
_state = _state.get("state_dict", _state)

def _w(name):
    return _state["sequence_transformer." + name].float()

_n1 = _RMSNorm(256).eval()
_n2 = _RMSNorm(256).eval()
_dense = _torch.nn.Linear(512, 256).eval()

_n1.load_state_dict({"g": _w("out_norm1.g")})
_n2.load_state_dict({"g": _w("out_norm2.g")})
_dense.load_state_dict({
    "weight": _w("seq_dense.weight"),
    "bias": _w("seq_dense.bias")
})

with _torch.no_grad():
    _x = _n1(_x)
    _pooled = _torch.cat(
        [_x.mean(1), _x.max(1).values], dim=-1
    )
    _pt = _n2(_dense(_pooled)).numpy()

_mx = _np.asarray(outputs[1].to_numpy(), dtype=_np.float32)

print("\\n=== FRESH PYTORCH vs CURRENT MAX SEQUENCE ===")
print("PYTORCH SHAPE:", _pt.shape)
print("MAX SHAPE:", _mx.shape)

if _pt.shape != _mx.shape:
    raise RuntimeError("Sequence shape mismatch")

_diff = _np.abs(_pt.astype(_np.float64) -
                _mx.astype(_np.float64))
print("MAX_DIFF:", float(_diff.max()))
print("MEAN_DIFF:", float(_diff.mean()))
print("MATCH:", bool(_np.allclose(
    _pt, _mx, rtol=1e-3, atol=1e-3
)))
'''

source = (
    source[:match.start()]
    + textwrap.indent(diagnostic, match.group(1))
    + source[match.start():]
)

exec(compile(source, str(runner), "exec"), {
    "__name__": "__main__",
    "__file__": str(runner),
})
PY
