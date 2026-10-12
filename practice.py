podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import runpy

sys.path.insert(0, "artifacts/v1.168-max")
sys.path.insert(0, "artifacts/v1.168-max/cta_max")

from cta_max.sequence_postprocess_max import SequencePostprocessMAX
from max.graph import Graph

original_call = SequencePostprocessMAX.__call__
original_output = Graph.output

def traced_call(self, x):
    print("POSTPROCESS INPUT:", x.shape, flush=True)
    result = original_call(self, x)
    print("POSTPROCESS OUTPUT:", result.shape, flush=True)
    return result

def traced_output(self, *values):
    print(
        "GRAPH DECLARED OUTPUTS:",
        [str(v.shape) for v in values],
        flush=True
    )
    return original_output(self, *values)

SequencePostprocessMAX.__call__ = traced_call
Graph.output = traced_output

runpy.run_path(
    "artifacts/v1.168-max/cta_max/run_transformer_sequence.py",
    run_name="__main__"
)
PY
