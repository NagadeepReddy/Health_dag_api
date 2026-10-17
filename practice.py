
podman run --rm -i \
  -v "$PWD:/cta:ro" -w /cta \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - serve --help <<'PY'
import importlib.util
import sys

path = "/cta/artifacts/v1.168-max/maxserve_cta_extension/cta_router.py"
spec = importlib.util.spec_from_file_location("cta_router", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.register_cta_routes()
print("CTA EXTENSION LOADED BEFORE MAX CLI", flush=True)

from max.entrypoints.pipelines import main
sys.argv[0] = "max"
main()
PY
