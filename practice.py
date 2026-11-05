
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)
BASE="localhost/cta-max-faiss:local"
IMAGE="localhost/pzaas-max-runtime:dev"
NAME="pzaas-deps-$$"

echo "=== PZAAS APPROVED PACKAGE SOURCE ==="

read -r -s -p "Enter approved Artifactory PyPI HTTPS index URL: " INDEX < /dev/tty
echo

case "$INDEX" in
  https://*) ;;
  *)
    echo "BLOCKED: A valid approved HTTPS package index is required"
    exit 1
    ;;
esac

TMP="$(mktemp -d "$PWD/.pzaas-pip.XXXXXX")"

cleanup() {
    "${PODMAN[@]}" rm -f "$NAME" >/dev/null 2>&1 || true
    rm -rf "$TMP"
}
trap cleanup EXIT

printf '[global]\nindex-url = %s\n' "$INDEX" > "$TMP/pip.conf"
chmod 600 "$TMP/pip.conf"
unset INDEX

echo "=== INSTALL REAL PZAAS DEPENDENCIES ==="

"${PODMAN[@]}" run \
  --name "$NAME" \
  --pull=never \
  --network=host \
  --memory=12g \
  --pids-limit=512 \
  -v "$TMP/pip.conf:/tmp/pip.conf:ro" \
  --entrypoint /bin/sh \
  "$BASE" -ec '
    set -eu
    unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL
    export PIP_CONFIG_FILE=/tmp/pip.conf
    /opt/venv/bin/python -m pip install \
      --no-cache-dir --disable-pip-version-check \
      "APScheduler>=3,<4" einops scikit-learn

    /opt/venv/bin/python -c "
from apscheduler.schedulers.background import BackgroundScheduler
import einops
import sklearn
import torch
import max
print(\"REAL PZAAS DEPENDENCIES: PASS\")
"
  '

"${PODMAN[@]}" commit "$NAME" "$IMAGE" >/dev/null
echo "PZAAS ISOLATED IMAGE: CREATED"

echo "=== NATIVE WORKER INITIALIZATION ==="

"${PODMAN[@]}" run --rm -i \
  --pull=never \
  --network=none \
  --memory=12g \
  --pids-limit=512 \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" -u - <<'PY'
import traceback

try:
    from pzaas_native_serve_dev.pzaas_spawn_worker import PZAASFactoryWrapper
    print("NATIVE FACTORY IMPORT: PASS", flush=True)

    pipeline = PZAASFactoryWrapper()()
    assert getattr(pipeline, "pzaas_native_adapter", None) is not None
    assert getattr(pipeline, "_pzaas_native_pipeline", False)

    print("NATIVE WORKER INITIALIZATION: PASS", flush=True)
    print("NEXT: BUILT-IN MAX SERVE HTTP 200", flush=True)

except Exception:
    print("NATIVE WORKER INITIALIZATION: BLOCKED", flush=True)
    traceback.print_exc()
    raise SystemExit(1)
PY
SH
