python - <<'PY'
from pathlib import Path
import shutil
import ast

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
s = p.read_text()

old = "sys.path.insert(0, str(BASE))"
new = "sys.path.insert(0, str(BASE.parent))"

if old in s:
    updated = s.replace(old, new, 1)
    updated = updated.replace(
        "from grecbase_fusion_order_correct_max import (",
        "from cta_max.grecbase_fusion_order_correct_max import (",
        1
    )
    ast.parse(updated)
    backup = p.with_suffix(".py.before_import_fix")
    if not backup.exists():
        shutil.copy2(p, backup)
    p.write_text(updated)
    print("MAX PACKAGE IMPORT FIXED")
elif new in s:
    print("PACKAGE PATH ALREADY PRESENT")
else:
    raise SystemExit("STOP: Runner source differs; nothing changed")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
