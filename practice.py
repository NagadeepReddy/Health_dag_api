podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v /application1/sajjna8/rt-pzai-bplan-v1:/workspace:ro \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
from pathlib import Path
import traceback

root = Path("/workspace/artifacts/v1.113-max/maxserve_bplan_extension")
weights = root / "bplan_max_dev/sibling_context_weights"
target = weights / "sibling_context_head.deep_embedding.0.weight.npy"

print("BPLAN CONTAINER WEIGHT CHECK", flush=True)
print("DIRECTORY EXISTS:", weights.is_dir(), flush=True)
print("TENSOR EXISTS:", target.is_file(), flush=True)
print("TENSOR COUNT:", len(list(weights.glob("sibling_context_head.*.npy"))), flush=True)

if not target.is_file():
    raise FileNotFoundError(f"Container cannot access: {target}")

print("BPLAN SIBLING WEIGHT ACCESS: PASS", flush=True)

try:
    from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel
    model = BPlanMAXModel()
    assert model.base is not None and model.head is not None
    print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
except Exception:
    print("BPLAN REAL MAX INITIALIZATION: NEXT BLOCKER", flush=True)
    traceback.print_exc()
    raise
PY
