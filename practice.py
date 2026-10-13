cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
set -e

python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
s = p.read_text()

old = "features(page, item, item_meta, item_pre, page_wide)"
new = "features(page, item, item_meta, item, page_wide)"

if s.count(old) != 1:
    raise SystemExit("STOP: Expected graph call not found. No change.")

updated = s.replace(old, new, 1)
ast.parse(updated)
p.write_text(updated)

print("UNDEFINED VARIABLE FIXED")
print("SEQUENCE EMBEDDING FIX PRESERVED")
print("FUSION ORDER AND SIBLING POOLING PRESERVED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
