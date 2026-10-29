cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

REPO="$PWD"
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
mkdir -p "$DEV"

test -f artifacts/v1.168-max/test-results/cta_max_tiles_smoketest_input.json
test -f artifacts/v1.168-max/cta_max/real_sanity_model_in.pt

timeout 240s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 2g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$REPO:/workspace:ro" \
  -v "$DEV:/output:rw" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys
import os
import json
import traceback
from pathlib import Path

import torch

base = Path("/workspace")
original = base / "artifacts/v1.168-max/cta_max/real_sanity_model_in.pt"
request = base / "artifacts/v1.168-max/test-results/cta_max_tiles_smoketest_input.json"
output = Path("/output/second_real_cta_model_in.pt")

assert not output.exists(), "STOP: Captured input already exists"

sys.path[:0] = [
    str(base / "artifacts/v1.168/core-artifact"),
    str(base / "artifacts/v1.168-max/utils/dependency-utils"),
    str(base / "artifacts/v1.168-max"),
]

class Captured(Exception):
    pass

reference = torch.load(original, map_location="cpu", weights_only=True)
assert isinstance(reference, dict), "STOP: Saved input format differs"

def trace_call(frame, event, arg):
    if event != "call" or frame.f_code.co_name != "predict_raw":
        return None
    if not frame.f_code.co_filename.endswith("/core-artifact/pipeline.py"):
        return None

    def trace_line(frame, event, arg):
        if event == "line" and "model_in" in frame.f_locals:
            value = frame.f_locals["model_in"]
            assert isinstance(value, dict), "STOP: model_in must be a dictionary"
            assert set(value) == set(reference), "STOP: Model input keys differ"
            torch.save(value, output)
            print("SECOND REAL MODEL INPUT: CAPTURED", flush=True)
            print("KEYS:", len(value), flush=True)
            print("FILE:", output, flush=True)
            raise Captured()
        return trace_line

    return trace_line

try:
    from pipeline import pipeline as CTA

    body = json.loads(request.read_text())
    assert isinstance(body, dict)

    pipeline = CTA()
    print("LOADING ORIGINAL DS PIPELINE", flush=True)
    pipeline.load()

    print("CAPTURING SECOND REAL REQUEST", flush=True)
    sys.settrace(trace_call)

    try:
        pipeline.predict_raw(body)
    except Captured:
        pass
    finally:
        sys.settrace(None)

    assert output.is_file(), "STOP: Model input capture did not occur"

    print("CAPTURE: PASS")
    print("ORIGINAL DS CODE: UNCHANGED")
    print("MAX GRAPH: UNCHANGED")

except Exception:
    sys.settrace(None)
    print("CAPTURE: FAIL")
    traceback.print_exc()
    sys.exit(1)
PY
SH
