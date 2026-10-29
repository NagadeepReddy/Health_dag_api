cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
test -s artifacts/v1.168/samples/sanity_input.json
test -s artifacts/v1.168-max/cta_max/real_sanity_model_in.pt
test ! -e "$DEV/third_distinct_cta_model_in.pt"

timeout -k 15s 240s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 4g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/output:rw" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u -B - <<'PY'
import sys, json
from pathlib import Path
import torch
import numpy as np

base = Path("/workspace")
sys.path[:0] = [
    str(base / "artifacts/v1.168/core-artifact"),
    str(base / "artifacts/v1.168-max/utils/dependency-utils"),
]

from cta_max.run_real_sanity_input_adapter import build_real_inputs
from pipeline import pipeline as CTA

reference = torch.load(
    base / "artifacts/v1.168-max/cta_max/real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)
request = json.loads(
    (base / "artifacts/v1.168/samples/sanity_input.json").read_text()
)

class Captured(Exception):
    pass

found = []

def trace(frame, event, arg):
    if event != "call" or frame.f_code.co_name != "predict_raw":
        return None
    if not frame.f_code.co_filename.endswith("/core-artifact/pipeline.py"):
        return None

    def watch(frame, event, arg):
        if event == "line":
            value = frame.f_locals.get("model_in")
            if isinstance(value, dict) and set(value) == set(reference):
                found.append(dict(value))
                raise Captured()
        return watch

    return watch

print("THIRD GENUINE CTA REQUEST: START", flush=True)
pipeline = CTA()
pipeline.load()

sys.settrace(trace)
try:
    pipeline.predict_raw(request)
except Captured:
    pass
finally:
    sys.settrace(None)

assert len(found) == 1, "STOP: Original DS model input not captured"

labels1, arrays1 = build_real_inputs(model_in=reference)
labels2, arrays2 = build_real_inputs(model_in=found[0])

assert labels1 == labels2, "STOP: Model input order differs"
assert len(arrays1) == len(arrays2) == 72

different = sum(
    not np.array_equal(np.asarray(a), np.asarray(b))
    for a, b in zip(arrays1, arrays2)
)

print("REAL MAX INPUT TENSORS:", len(arrays2), flush=True)
print("DIFFERENT INPUT TENSORS:", different, flush=True)

if different:
    dest = Path("/output/third_distinct_cta_model_in.pt")
    assert not dest.exists()
    torch.save(found[0], dest)
    print("DISTINCT REAL MODEL INPUT: READY")
    print("FILE:", dest)
else:
    print("DISTINCT MODEL INPUT: NOT AVAILABLE FROM THIS SAMPLE")
    print("NEXT REQUIREMENT: A genuinely different CTA request")

print("ORIGINAL DS CODE: UNCHANGED")
print("MAX EXECUTION: NOT PERFORMED")
PY
SH
