python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
source = p.read_text()

old = "    result = np.asarray(output)"
new = "    result = np.asarray(output, dtype=np.float32)"

if source.count(old) == 1:
    updated = source.replace(old, new, 1)
    ast.parse(updated, filename=str(p))

    backup = p.with_suffix(".py.before_output_dtype_fix")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("MAX OUTPUT CONVERSION FIXED")
    print("BACKUP:", backup)
elif new in source:
    print("MAX OUTPUT CONVERSION ALREADY FIXED")
else:
    raise SystemExit("STOP: Expected output line not found; nothing changed")

print("ORIGINAL PYTORCH/DS FILES UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
