REPO=/application1/sajjna8/rt-pzai-bplan-v1
OUT="$REPO/artifacts/v1.113-max/maxserve_bplan_extension"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:/workspace:ro" \
  -v "$OUT:/bplan_out:rw" \
  -w /workspace/artifacts/v1.113/core-artifact \
  localhost/cta-max-faiss:local - <<'PY'
import json, time, traceback
from pathlib import Path

try:
    from pipeline import pipeline

    body = json.loads(
        Path("/bplan_out/bplan_sanity_features.json").read_text()
    )

    model = pipeline()
    calls = [0]
    original_inference = model.inference

    def tracked_inference(*args, **kwargs):
        calls[0] += 1
        return original_inference(*args, **kwargs)

    model.inference = tracked_inference

    start = time.time()
    response = model.predict_raw(body)

    Path("/bplan_out/bplan_pytorch_baseline.json").write_text(
        json.dumps(response, indent=2, default=str)
    )

    print("PYTORCH BASELINE: PASS")
    print("NEURAL INFERENCE CALLS:", calls[0])
    print("ELAPSED SECONDS:", round(time.time() - start, 2))
    print("BASELINE SAVED: /bplan_out/bplan_pytorch_baseline.json")

except Exception:
    print("PYTORCH BASELINE: FAILED")
    traceback.print_exc()
    raise SystemExit(1)
PY
