podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import runpy
import inspect
import numpy as np
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, str(base))
sys.path.insert(0, "artifacts/v1.168-max")

import parallel_transformer_graph_sequence as module

print("GRAPH LOADED:", module.__file__)

source = inspect.getsource(
    module.build_parallel_transformer_graph
)

assert "graph.output(postprocess(output))" in source, \
    "STOP: loaded graph does not apply postprocessing"

print("POSTPROCESS CONNECTION: CONFIRMED")

runpy.run_path(
    str(base / "run_transformer_sequence.py"),
    run_name="__main__"
)

out = np.load(base / "sequence_combined_output.npy")

print("COMBINED OUTPUT SHAPE:", out.shape)
print("FINITE:", bool(np.isfinite(out).all()))
print("EXPECTED SHAPE:", (1, 256))
print("INTEGRATION PASS:", out.shape == (1, 256))
PY
