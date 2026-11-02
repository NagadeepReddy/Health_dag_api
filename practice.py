podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v /application1/sajjna8/rt-pzai-bplan-v1:/workspace:ro \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import traceback

print("BPLAN REAL MAX INITIALIZATION: START", flush=True)

try:
    from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel
    model = BPlanMAXModel()

    assert model.base is not None
    assert model.head is not None

    print("BPLAN BASE GRAPH: PASS", flush=True)
    print("BPLAN PREDICTION HEAD: PASS", flush=True)
    print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
    print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
except Exception:
    print("BPLAN INITIALIZATION: NOT YET PASSING", flush=True)
    traceback.print_exc()
    raise
PY
