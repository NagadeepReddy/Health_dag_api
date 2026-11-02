set -e
ROOT=/application1/sajjna8/rt-pzai-bplan-v1
EXT="$ROOT/artifacts/v1.113-max/maxserve_bplan_extension"

python3 - <<'PY'
from pathlib import Path

ext = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
file = ext / "bplan_max_dev/att_pooling_max.py"
weight = ext / "bplan_helper_weights_stage/grecbase_integration_weights/att_pooling.norm1.g.npy"

assert file.is_file(), "STOP: integration file missing"
assert weight.is_file(), "STOP: pooling weight missing"

source = file.read_text()
old = str(weight)
new = 'str(__import__("pathlib").Path(__file__).resolve().parents[1] / "bplan_helper_weights_stage" / "grecbase_integration_weights" / "att_pooling.norm1.g.npy")'

assert source.count(old) == 1, "STOP: unexpected path structure"
updated = source.replace("'" + old + "'", new)
assert updated != source, "STOP: expected quoted path not found"

compile(updated, str(file), "exec")
file.write_text(updated)

print("BPLAN POOLING PORTABLE PATH: PASS", flush=True)
print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
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

print("BPLAN MAX INITIALIZATION: START", flush=True)
model = BPlanMAXModel()
assert model.base is not None and model.head is not None
print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
PY
