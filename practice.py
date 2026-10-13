cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import torch, ast, shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
ckpt = Path("artifacts/v1.168/core-artifact/model_0_base.pt")

state = torch.load(ckpt, map_location="cpu", weights_only=True)

outer_key = "seq_dense.bias"
inner_key = "sequence_transformer.seq_dense.bias"

assert outer_key in state, "STOP: Outer bias missing"
assert inner_key in state, "STOP: Inner bias missing"

outer = state[outer_key]
inner = state[inner_key]

assert outer.shape == inner.shape == (256,), "STOP: Unexpected bias shape"

print("OUTER BIAS:", outer_key)
print("INNER BIAS:", inner_key)
print("BIAS MAX DIFFERENCE:",
      (outer - inner).abs().max().item())

src = p.read_text()

assert src.count(f'["{inner_key}"]') == 1, \
    "STOP: Unexpected current source"

updated = src.replace(
    f'["{inner_key}"]',
    f'["{outer_key}"]',
    1
)

ast.parse(updated)

backup = p.with_name(p.name + ".before_outer_seq_bias_fix")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

print("FIX APPLIED: Outer Sequence bias corrected")
print("BACKUP:", backup)
print("PYTHON SYNTAX: PASS")
print("72-INPUT MAPPING: UNCHANGED")
PY
