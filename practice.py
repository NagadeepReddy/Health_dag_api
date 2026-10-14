podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import numpy as np
from pathlib import Path
from max.driver import CPU
from max.graph import DeviceRef

b = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, str(b))

from run_real_sanity_input_adapter import build_real_inputs
from cta_max.grecbase_fusion_order_correct_max import build_grecbase_fusion_graph_order_correct

labels, arrays = build_real_inputs()
graph = build_grecbase_fusion_graph_order_correct(DeviceRef.from_device(CPU()))

def shape(x):
    return tuple(int(v) for v in x.shape)

real = [shape(np.asarray(a)) for a in arrays]
expected = []
for inp in graph.inputs:
    try:
        expected.append(shape(inp.type))
    except (TypeError, ValueError):
        expected.append(None)

print("SAVED INPUTS:", len(real))
print("GRAPH INPUTS:", len(expected))

candidates = []
if len(real) == len(expected) + 1:
    for skip in range(len(real)):
        reduced = real[:skip] + real[skip+1:]
        if all(e is None or r == e for r, e in zip(reduced, expected)):
            candidates.append(skip)

print("\n=== EXTRA INPUT CANDIDATES ===")
for i in candidates[:15]:
    print(i, labels[i], real[i])

print("\n=== FINAL 15 INPUT MAPPINGS ===")
for i in range(max(0, len(real)-15), len(real)):
    print(i, labels[i], real[i],
          "GRAPH:", expected[i] if i < len(expected) else "NO GRAPH INPUT")

print("\nCANDIDATE COUNT:", len(candidates))
PY
