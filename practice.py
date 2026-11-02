
REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, json, traceback, gc
from pathlib import Path

root = Path("artifacts/v1.113").resolve()
ext = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()

sys.path.insert(0, str(root / "core-artifact"))
sys.path.insert(0, str(root / "utils/dependency-utils"))
sys.path.insert(0, str(ext / "bplan_max_dev"))

try:
    import pipeline
    from bplan_max_model_adapter import BPlanMAXModel

    print("LOADING ORIGINAL BPLAN PIPELINE...", flush=True)
    ds = pipeline.pipeline()
    ds.load()
    assert ds.loaded
    print("ORIGINAL PIPELINE LOAD: PASS", flush=True)

    # Replace only the inference backend in memory.
    ds.bplan_model = None
    gc.collect()

    class TrackedMAX:
        calls = 0

        def __init__(self):
            self.model = BPlanMAXModel()

        def __call__(self, **kwargs):
            self.calls += 1
            print("BPLAN MAX NEURAL INFERENCE CALLED", flush=True)
            return self.model(**kwargs)

    backend = TrackedMAX()
    ds.bplan_model = backend
    print("BPLAN MAX BACKEND ATTACHED: PASS", flush=True)

    samples = root / "core-artifact/test_samples"

    for name in ("test_sample_1.json", "test_sample_2.json"):
        path = samples / name
        if not path.is_file():
            continue

        body = json.loads(path.read_text())
        before = backend.calls
        print("TESTING:", name, flush=True)

        result = ds.predict_raw(body)

        print("MAX CALLS:", backend.calls - before, flush=True)
        print("RESPONSE TYPE:", type(result).__name__, flush=True)

        if isinstance(result, dict):
            print("RESPONSE KEYS:", list(result)[:10])
            prediction = result.get("jsonData", {}).get("prediction", {})
            print("PREDICTION KEYS:", list(prediction)[:10])

        if backend.calls > 0:
            assert isinstance(result, dict)
            assert "inference_raw" in ds.transactionMetadata, \
                "STOP: MAX called but ranking completion not verified"
            assert "jsonData" in result
            assert "prediction" in result["jsonData"]
            print("BPLAN MAX JSON E2E: PASS", flush=True)
            break
    else:
        raise RuntimeError(
            "No test sample exercised neural inference; JSON E2E unverified"
        )

    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN MAX JSON E2E: NOT YET PASSED", flush=True)
    traceback.print_exc()
    sys.exit(1)
PY
