
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)
W=/vzwhome/sajjna8/pzaas_wheels
D=/application1/max_shared_python_deps
IMAGE=localhost/cta-max-faiss:local

test -d "$W" || { echo "ERROR: Transferred wheels missing"; exit 1; }
mkdir -p "$D"

echo "=== INSTALL SHARED DEPENDENCIES WITHOUT CHANGING IMAGE ==="

"${P[@]}" run --rm --pull=never --network=none \
  -v "$W:/wheels:ro" \
  -v "$D:/shared_deps" \
  -v "$PWD:/workspace:ro" \
  --entrypoint /bin/sh "$IMAGE" -ec '
    set -e

    /opt/venv/bin/python -m pip install \
      --no-index \
      --find-links=/wheels \
      --target=/shared_deps \
      "APScheduler>=3,<4"

    PYTHONPATH=/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps \
      /opt/venv/bin/python -c "
from apscheduler.schedulers.background import BackgroundScheduler
import einops
import sklearn
import torch
import faiss
import max
print('PZAAS SHARED RUNTIME DEPENDENCIES: PASS')
"
  '

echo "EXISTING CTA/BPLAN IMAGE: UNCHANGED"
echo "NEXT: PZAAS NATIVE WORKER INITIALIZATION"
SH
