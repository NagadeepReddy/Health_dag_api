REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, json, gc, hashlib, traceback
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

    sample = root / "core-artifact/test_samples/test_sample_1.json"
    body = json.loads(sample.read_text())

    ds = pipeline.pipeline()
    ds.load()
    print("ORIGINAL PIPELINE: PASS", flush=True)

    print("RUNNING ORIGINAL PYTORCH JSON...", flush=True)
    original = ds.predict_raw(body)
    assert "inference_raw" in ds.transactionMetadata
    original_prediction = original["jsonData"]["prediction"]
    print("ORIGINAL PYTORCH JSON: PASS", flush=True)

    # Release original neural models; preserve DS code and artifacts.
    ds.bplan_model = None
    ds.base_model = None
    gc.collect()

    class TrackedMAX:
        calls = 0

        def __init__(self):
            self.model = BPlanMAXModel()

        def __call__(self, **kwargs):
            self.calls += 1
            return self.model(**kwargs)

    backend = TrackedMAX()
    ds.bplan_model = backend

    # Clear previous run metadata before validating MAX.
    ds.transactionMetadata = {}

    print("RUNNING MODULAR MAX JSON...", flush=True)
    result = ds.predict_raw(body)

    assert backend.calls == 1, (
        f"STOP: expected 1 MAX inference call, got {backend.calls}"
    )
    assert "inference_raw" in ds.transactionMetadata, \
        "STOP: MAX ranking not completed"

    max_prediction = result["jsonData"]["prediction"]

    def canonical(value):
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, default=str
        )

    before = canonical(original_prediction)
    after = canonical(max_prediction)

    print("MAX NEURAL CALLS:", backend.calls)
    print("PYTORCH PREDICTION SHA256:",
          hashlib.sha256(before.encode()).hexdigest())
    print("MAX PREDICTION SHA256:",
          hashlib.sha256(after.encode()).hexdigest())

    if before != after:
        print("BPLAN BUSINESS JSON PARITY: NOT YET PASSED")
        if isinstance(original_prediction, dict) and isinstance(max_prediction, dict):
            for key in sorted(set(original_prediction) | set(max_prediction)):
                if canonical(original_prediction.get(key)) != canonical(max_prediction.get(key)):
                    print("DIFFERENT PREDICTION FIELD:", key)
        sys.exit(2)

    print("BPLAN BUSINESS JSON PARITY: PASS")
    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN BUSINESS JSON VALIDATION: FAILED")
    traceback.print_exc()
    sys.exit(1)
PY
