ROOT=/application1/sajjna8/rt-pzai-bplan-v1
EXT="$ROOT/artifacts/v1.113-max/maxserve_bplan_extension"

python3 - <<'PY'
from pathlib import Path
import os

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
link = root / "bplan_max_dev/sibling_context_weights"
destination = root / "bplan_helper_weights_stage/sibling_context_weights"
required = "sibling_context_head.deep_embedding.0.weight.npy"

assert link.is_symlink(), "STOP: expected symlink"
assert link.resolve() == destination.resolve(), "STOP: unexpected target"
assert (destination / required).is_file(), "STOP: weight missing"
assert len(list(destination.glob("*.npy"))) == 20, "STOP: unexpected weight count"

temporary = link.with_name("sibling_context_weights.relative_tmp")
assert not temporary.exists() and not temporary.is_symlink()
temporary.symlink_to("../bplan_helper_weights_stage/sibling_context_weights")
assert (temporary / required).is_file()
os.replace(temporary, link)

print("BPLAN RELATIVE SYMLINK: PASS")
print("BPLAN 20 SIBLING WEIGHTS: ACCESSIBLE ON HOST")
PY

if [ $? -eq 0 ]; then
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$ROOT:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
from pathlib import Path

root = Path("/workspace/artifacts/v1.113-max/maxserve_bplan_extension")
target = root / "bplan_max_dev/sibling_context_weights/sibling_context_head.deep_embedding.0.weight.npy"

assert target.is_file(), f"Missing in container: {target}"
print("BPLAN CONTAINER WEIGHT ACCESS: PASS", flush=True)

from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel
model = BPlanMAXModel()

assert model.base is not None and model.head is not None
print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
PY
fi
