
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'RUN'
set -euo pipefail

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)
BASE=localhost/cta-max-faiss:local
IMAGE=localhost/pzaas-max-runtime:dev
NAME="pzaas-build-$$"

trap '"${P[@]}" rm -f "$NAME" >/dev/null 2>&1 || true' EXIT

echo "=== INSTALL REAL APSCHEDULER IN PZAAS CONTAINER ==="

"${P[@]}" run --name "$NAME" --pull=never --network=host \
  --memory=12g --pids-limit=512 \
  --entrypoint /bin/sh "$BASE" -ec '
    set -eu
    /opt/venv/bin/python -m pip install \
      -q --disable-pip-version-check --no-cache-dir \
      "APScheduler>=3,<4"

    /opt/venv/bin/python -c "
from apscheduler.schedulers.background import BackgroundScheduler
import torch
import max
print(\"REAL APSCHEDULER AND MAX: PASS\", flush=True)
"
  '

"${P[@]}" commit "$NAME" "$IMAGE" >/dev/null

echo "PZAAS ISOLATED IMAGE: CREATED"
echo "=== PZAAS NATIVE WORKER INITIALIZATION ==="

"${P[@]}" run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$PWD:/workspace:ro" -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" -u - <<'PY'
from pzaas_native_serve_dev.pzaas_spawn_worker import PZAASFactoryWrapper

import einops
import sklearn

print("NATIVE FACTORY AND LOCAL DEPENDENCIES: PASS", flush=True)

pipeline = PZAASFactoryWrapper()()

assert getattr(pipeline, "pzaas_native_adapter", None) is not None
assert getattr(pipeline, "_pzaas_native_pipeline", False)

print("NATIVE WORKER INITIALIZATION: PASS", flush=True)
print("NEXT: BUILT-IN MAX SERVE HTTP 200", flush=True)
PY
RUN
