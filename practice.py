cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

for IMAGE in \
  localhost/cta-max-faiss:local \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  docker-remote.oneartifactoryci.verizon.com/modular/max-nvidia-full:latest
do
  echo "=== $IMAGE ==="

  timeout 20s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm --pull=never \
    --network=none --read-only \
    --memory=512m --pids-limit=16 \
    --tmpfs /tmp:rw,size=64m,mode=1777 \
    -e HOME=/tmp \
    -e XDG_CACHE_HOME=/tmp \
    -e PYTHONDONTWRITEBYTECODE=1 \
    --entrypoint /bin/sh \
    "$IMAGE" \
    -c '
      if [ -x /opt/venv/bin/python3 ]; then
        PY=/opt/venv/bin/python3
      else
        PY=python3
      fi
      "$PY" -B -c "
import importlib.util
from importlib.metadata import version, PackageNotFoundError

for module in ('faiss', 'max'):
    print(module.upper(), 'PRESENT' if importlib.util.find_spec(module) else 'MISSING')

for package in ('faiss-cpu', 'modular'):
    try:
        print(package, 'VERSION:', version(package))
    except PackageNotFoundError:
        print(package, 'VERSION: NOT REGISTERED')
"
    '

  echo "CHECK EXIT CODE: $?"
done
