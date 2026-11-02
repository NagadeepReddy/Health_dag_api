set -e

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
EXT="$ROOT/artifacts/v1.113-max/maxserve_bplan_extension"

python3 - <<'PY'
from pathlib import Path
import re

ext = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
file = ext / "bplan_max_dev/att_pooling_max.py"
weights = ext / "bplan_helper_weights_stage/grecbase_integration_weights"

assert file.is_file() and weights.is_dir()

source = file.read_text()
prefix = re.escape(str(weights) + "/")
pattern = re.compile(r"""(['"])""" + prefix + r"""([^'"]+\.npy)\1""")

names = [m.group(2) for m in pattern.finditer(source)]
assert "att_pooling.norm2.g.npy" in names, "STOP: expected path not found"

for name in names:
    assert (weights / name).is_file(), f"STOP: missing weight {name}"

def replace(match):
    name = match.group(2)
    return (
        'str(__import__("pathlib").Path(__file__).resolve().parents[1]'
        ' / "bplan_helper_weights_stage"'
        ' / "grecbase_integration_weights"'
        f' / "{name}")'
    )

updated, count = pattern.subn(replace, source)
compile(updated, str(file), "exec")
file.write_text(updated)

print("BPLAN POOLING PORTABLE PATHS: PASS")
print("REFERENCES FIXED:", count)
print("ORIGINAL DS AND CTA: UNCHANGED")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$ROOT:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel

print("BPLAN REAL MAX INITIALIZATION: START", flush=True)
model = BPlanMAXModel()

assert model.base is not None
assert model.head is not None

print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
PY
