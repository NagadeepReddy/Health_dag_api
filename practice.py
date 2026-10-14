cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
import importlib.util
s = importlib.util.find_spec("faiss")
print("HOST FAISS:", s.origin if s else "NOT INSTALLED")
PY

echo "LOCAL FAISS WHEELS:"
find /application/sajjna8 /application/miniconda3 /root/.cache/pip \
  -type f -iname '*faiss*.whl' -print 2>/dev/null | head -10

echo "MAX CONTAINER PYTHON:"
podman run --rm \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  --version
