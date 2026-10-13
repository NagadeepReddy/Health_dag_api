python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
s = p.read_text()

old = "result = np.asarray(output, dtype=np.float32)"
new = "result = np.asarray(output.to_numpy(), dtype=np.float32)"

if old in s and s.count(old) == 1:
    updated = s.replace(old, new, 1)
    ast.parse(updated, filename=str(p))

    backup = p.with_suffix(".py.before_tensor_conversion_fix")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("MAX TENSOR CONVERSION FIXED")
elif new in s:
    print("FIX ALREADY PRESENT")
else:
    raise SystemExit("STOP: Expected line not found; nothing changed")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
