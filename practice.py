cd /application1/sajjna8/rt-pzaas-v1.0 && \
python3 - <<'PY'
from pathlib import Path
import subprocess, shutil, sys

dst = Path("artifacts/v1.472-max/pzaas_max/validation/python_deps/einops")

candidates = list(dict.fromkeys([
    sys.executable,
    "/usr/local/bin/python3",
    "/usr/bin/python3",
    "/opt/venv/bin/python"
]))

for exe in candidates:
    if not Path(exe).is_file():
        continue
    try:
        result = subprocess.run(
            [exe, "-c",
             "import importlib.util; s=importlib.util.find_spec('einops'); print(s.origin if s else '')"],
            capture_output=True, text=True, timeout=8
        )
        source = Path(result.stdout.strip())
        if result.returncode == 0 and source.is_file() and source.name == "__init__.py":
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source.parent, dst, dirs_exist_ok=True)
            print("REAL EINOPS STAGED:", source.parent)
            print("ORIGINAL DS: UNCHANGED")
            break
    except (OSError, subprocess.TimeoutExpired, ValueError):
        continue
else:
    print("HOST EINOPS: UNAVAILABLE")
    print("APPROVED OFFLINE WHEEL REQUIRED")
    sys.exit(2)
PY

if [ -f artifacts/v1.472-max/pzaas_max/validation/python_deps/einops/__init__.py ]; then
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage run --rm \
    --network none --memory 2g \
    -e PYTHONPATH=/deps \
    -v "$PWD/artifacts/v1.472-max/pzaas_max/validation/python_deps:/deps:ro" \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    -c 'import einops; print("PZAAS EINOPS: PASS", einops.__version__)'
fi
