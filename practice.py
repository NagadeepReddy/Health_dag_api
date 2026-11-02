P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

for MODE in pytorch max; do
  echo "=== $MODE NUMERICAL INFERENCE ==="

  "${P[@]}" exec -i -e BPLAN_PARITY_MODE="$MODE" \
    bplan-debug /opt/venv/bin/python - <<'PY'
import os, gc, json
import numpy as np
from pathlib import Path
from pipeline import pipeline

mode = os.environ["BPLAN_PARITY_MODE"]
sample = Path(
    "/workspace/artifacts/v1.113/core-artifact/"
    "test_samples/test_sample_1.json"
)

model = pipeline()
model.load()

if mode == "max":
    model.bplan_model = None
    model.base_model = None
    gc.collect()
    from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel
    backend = BPlanMAXModel()
else:
    backend = model.bplan_model

class Capture:
    def __init__(self, backend):
        self.backend = backend
        self.outputs = []

    def __call__(self, **kwargs):
        result = self.backend(**kwargs)
        arr = result.detach().cpu().numpy() if hasattr(
            result, "detach"
        ) else np.asarray(result)
        self.outputs.append(np.array(arr, copy=True))
        return result

capture = Capture(backend)
model.bplan_model = capture

body = json.loads(sample.read_text())
model.predict_raw(body)

if not capture.outputs:
    raise RuntimeError("No model inference executed")

np.savez(
    f"/tmp/bplan_{mode}_scores.npz",
    **{f"call_{i}": x for i, x in enumerate(capture.outputs)}
)
print(mode.upper(), "MODEL CALLS:", len(capture.outputs))
print("OUTPUT SHAPES:", [x.shape for x in capture.outputs])
print(mode.upper(), "SCORES SAVED", flush=True)
PY

  if [ $? -ne 0 ]; then
    echo "STOP: $MODE execution failed"
    break
  fi
done

"${P[@]}" exec bplan-debug /opt/venv/bin/python - <<'PY'
import numpy as np
from pathlib import Path

a = Path("/tmp/bplan_pytorch_scores.npz")
b = Path("/tmp/bplan_max_scores.npz")

if not a.exists() or not b.exists():
    print("NUMERICAL PARITY: INCOMPLETE")
    raise SystemExit(1)

with np.load(a) as pt, np.load(b) as mx:
    print("\n=== BPLAN NUMERICAL PARITY ===")
    print("MODEL CALL COUNTS:", len(pt.files), len(mx.files))

    if pt.files != mx.files:
        raise SystemExit("FAIL: Model call counts differ")

    passed = True
    for key in pt.files:
        x, y = pt[key], mx[key]
        print(key, "SHAPES:", x.shape, y.shape)
        if x.shape != y.shape:
            passed = False
            continue
        finite = np.isfinite(x).all() and np.isfinite(y).all()
        close = finite and np.allclose(x, y, rtol=1e-4, atol=1e-3)
        print("MAX ABS DIFFERENCE:", float(np.max(np.abs(x-y))))
        print("ALLCLOSE:", close)
        passed &= close

    print("BPLAN NUMERICAL PARITY:", "PASS" if passed else "FAIL")
PY
