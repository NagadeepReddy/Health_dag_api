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
dev = Path("artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev").resolve()

sys.path[:0] = [
    str(root / "core-artifact"),
    str(root / "utils/dependency-utils"),
    str(dev),
]

import pipeline
from bplan_max_model_adapter import BPlanMAXModel

ds = pipeline.pipeline()
ds.load()
print("ORIGINAL PIPELINE LOAD: PASS", flush=True)

ds.bplan_model = None
gc.collect()

class TrackedMAX:
    calls = 0

    def __init__(self):
        self.model = BPlanMAXModel()

    def __call__(self, **kwargs):
        self.calls += 1
        print("MAX BACKEND CALLED:", self.calls, flush=True)
        try:
            result = self.model(**kwargs)
            print("MAX BACKEND OUTPUT:", tuple(result.shape), flush=True)
            return result
        except Exception:
            print("MAX BACKEND EXCEPTION:", flush=True)
            traceback.print_exc()
            raise

backend = TrackedMAX()
ds.bplan_model = backend

original_inference = ds.inference
original_postprocess = ds.postprocess

def traced_inference(*args, **kwargs):
    print("ENTER ORIGINAL INFERENCE", flush=True)
    try:
        result = original_inference(*args, **kwargs)
        print("ORIGINAL RANKING: PASS", flush=True)
        return result
    except Exception:
        print("ORIGINAL INFERENCE EXCEPTION:", flush=True)
        traceback.print_exc()
        raise

def traced_postprocess(*args, **kwargs):
    print("ENTER ORIGINAL POSTPROCESS", flush=True)
    try:
        result = original_postprocess(*args, **kwargs)
        print("ORIGINAL POSTPROCESS: PASS", flush=True)
        return result
    except Exception:
        print("ORIGINAL POSTPROCESS EXCEPTION:", flush=True)
        traceback.print_exc()
        raise

ds.inference = traced_inference
ds.postprocess = traced_postprocess

sample = root / "core-artifact/test_samples/test_sample_1.json"
body = json.loads(sample.read_text())

print("RUNNING ORIGINAL JSON FLOW...", flush=True)
result = ds.predict_raw(body)

print("MAX CALLS:", backend.calls)
print("RANKING RECORDED:", "inference_raw" in ds.transactionMetadata)
print("RESPONSE TYPE:", type(result).__name__)
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
