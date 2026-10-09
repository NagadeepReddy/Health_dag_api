podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import importlib.util
from max.graph import ops

p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

try:
    spec=importlib.util.spec_from_file_location("ptb", p)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    print("MODULE IMPORT: SUCCESS")
except Exception as e:
    print("MODULE IMPORT ERROR:", type(e).__name__, e)

needed = [
    "arange", "concat", "cos", "sin",
    "reshape", "transpose", "permute",
    "matmul", "softmax", "where",
    "broadcast_to", "unsqueeze"
]

for n in needed:
    print(f"{n:12} :", hasattr(ops, n))
PY
