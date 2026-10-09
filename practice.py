python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_context_head_wide.py")
s = p.read_text()

s = s.replace(
    "from max.graph import DeviceRef",
    "from max.graph import DeviceRef, Shape"
)
s = s.replace(
    "from max.graph.weights import Shape, WeightData",
    "from max.graph.weights import WeightData"
)

p.write_text(s)
print("WIDE SHAPE IMPORT FIXED")
PY
