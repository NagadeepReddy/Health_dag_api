REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, json, traceback
from pathlib import Path

root = Path("artifacts/v1.113").resolve()
dev = Path("artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev").resolve()

sys.path[:0] = [
    str(root / "core-artifact"),
    str(root / "utils/dependency-utils"),
    str(dev),
]

try:
    import pipeline
    from bplan_max_model_adapter import BPlanMAXModel
    from bplan_native_worker_adapter import BPlanNativeWorkerAdapter

    worker = BPlanNativeWorkerAdapter(
        pipeline_factory=pipeline.pipeline,
        max_factory=BPlanMAXModel,
    )

    sample = root / "core-artifact/test_samples/test_sample_1.json"
    body = json.loads(sample.read_text())

    print("INITIALIZING BPLAN WORKER...", flush=True)
    result = worker.predict(body)

    assert worker.max_calls == 1, "MAX neural inference not called"
    assert "inference_raw" in worker.pipeline.transactionMetadata
    assert isinstance(result, dict)
    assert isinstance(result["jsonData"]["prediction"], dict)

    print("BPLAN NATIVE WORKER: PASS")
    print("MAX NEURAL CALLS:", worker.max_calls)
    print("BPLAN JSON RESPONSE: PASS")
    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN WORKER VALIDATION: FAILED")
    traceback.print_exc()
    sys.exit(1)
PY
