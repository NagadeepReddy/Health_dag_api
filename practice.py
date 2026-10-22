cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=8g --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  f30453065dac \
  -u -c '
import faulthandler
faulthandler.dump_traceback_later(20, repeat=False)
print("PYTHON START: PASS", flush=True)
print("IMPORTING MAX CTA FACTORY...", flush=True)
from maxserve_cta_extension.cta_scheduler_factory import create_cta_scheduler
faulthandler.cancel_dump_traceback_later()
print("REAL MAX CTA FACTORY IMPORT: PASS", flush=True)
'

echo "EXIT CODE: $?"
