cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=8g --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  --entrypoint /opt/venv/bin/python \
  f30453065dac \
  -u -c '
import sys
from pathlib import Path

root = Path("/workspace/artifacts")
ds = root / "v1.168/core-artifact"
sys.path.insert(0, str(ds))

assert (ds / "pipeline.py").is_file()
print("CTA PIPELINE PATH: PASS", flush=True)

from pipeline import CTA
print("REAL CTA PIPELINE IMPORT: PASS", flush=True)
'

echo "EXIT CODE: $?"
