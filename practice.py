podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import numpy as np
from pathlib import Path
from max.driver import CPU
from max.graph import DeviceRef

root = Path("artifacts/v1.168-max").resolve()
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "cta_max"))

from run_real_sanity_input_adapter import build_real_inputs
from cta_max.grecbase_fusion_order_correct_max import build_grecbase_fusion_graph_order_correct

labels, arrays = build_real_inputs()
graph = build_grecbase_fusion_graph_order_correct(
    DeviceRef.from_device(CPU())
)

real = [tuple(np.asarray(x).shape) for x in arrays]

def graph_shape(x):
    try:
        return tuple(int(d) for d in x.type.shape)
    except (TypeError, ValueError, AttributeError):
        return None

expected = [graph_shape(x) for x in graph.inputs]

print("REAL INPUTS:", len(real))
print("GRAPH INPUTS:", len(expected))

candidates = []
if len(real) == len(expected) + 1:
    for skip in range(len(real)):
        reduced = real[:skip] + real[skip+1:]
        if all(e is None or r == e
               for r, e in zip(reduced, expected)):
            candidates.append(skip)

print("\n=== POSSIBLE EXTRA INPUTS ===")
for i in candidates[:20]:
    print(i, labels[i], real[i])

print("Candidate count:", len(candidates))

print("\n=== LAST 10 INPUTS ===")
for i in range(max(0, len(real)-10), len(real)):
    print(i, labels[i], real[i],
          "GRAPH:", expected[i] if i < len(expected) else "NONE")
PY
