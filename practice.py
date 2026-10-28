cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

for IMAGE in \
  localhost/cta-max-faiss:local \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  docker-remote.oneartifactoryci.verizon.com/modular/max-nvidia-full:latest
do
  echo "=== IMAGE: $IMAGE ==="

  timeout 30s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run -i --rm --pull=never \
    --network=none --read-only \
    --memory=512m --pids-limit=16 \
    -e PYTHONDONTWRITEBYTECODE=1 \
    --entrypoint /opt/venv/bin/python3 \
    "$IMAGE" -S -B - <<'PY'
import importlib.util
from importlib.metadata import version, PackageNotFoundError

for module in ("faiss", "max"):
    try:
        found = importlib.util.find_spec(module)
        print(f"{module.upper()}: {'PRESENT' if found else 'MISSING'}")
    except Exception as exc:
        print(f"{module.upper()}: CHECK ERROR: {exc}")

for package in ("faiss-cpu", "modular"):
    try:
        print(f"{package}: {version(package)}")
    except PackageNotFoundError:
        print(f"{package}: VERSION NOT REGISTERED")
PY

  echo "CHECK EXIT CODE: $?"
done
