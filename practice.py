cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

for IMAGE in \
  localhost/cta-max-faiss:local \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  docker-remote.oneartifactoryci.verizon.com/modular/max-nvidia-full:latest
do
  echo "=== $IMAGE ==="

  timeout 25s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run -i --rm --pull=never \
    --network=none --read-only \
    --memory=512m --pids-limit=16 \
    --tmpfs /tmp:rw,size=64m,mode=1777 \
    --tmpfs /root/.cache:rw,size=64m,mode=1777 \
    -e HOME=/tmp \
    -e XDG_CACHE_HOME=/tmp \
    -e PYTHONDONTWRITEBYTECODE=1 \
    --entrypoint /opt/venv/bin/python3 \
    "$IMAGE" -B - <<'PY'
import importlib.util
from importlib.metadata import version, PackageNotFoundError

for module in ("faiss", "max"):
    try:
        print(module.upper(), "PRESENT" if importlib.util.find_spec(module) else "MISSING")
    except Exception as exc:
        print(module.upper(), "CHECK ERROR:", exc)

for package in ("faiss-cpu", "modular"):
    try:
        print(package, "VERSION:", version(package))
    except PackageNotFoundError:
        print(package, "NOT REGISTERED")
PY

  echo "CHECK EXIT CODE: $?"
done
