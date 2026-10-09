python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_context_head_wide.py")
s = p.read_text()

s = s.replace(
    "from max.graph import DeviceRef, WeightData",
    "from max.graph import DeviceRef"
)
s = s.replace(
    "from max.graph.weights import Shape",
    "from max.graph.weights import Shape, WeightData"
)

p.write_text(s)
print("WIDE WEIGHTDATA IMPORT FIXED")
PY
