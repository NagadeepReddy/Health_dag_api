
cd /application1/sajjna8/rt-pzaas-v1.0 && \
APSWHEEL="$(find /application1/sajjna8 /root/.cache/pip \
-type f -iname 'apscheduler-3*.whl' -print -quit 2>/dev/null)" && \
if [ -z "$APSWHEEL" ]; then
  echo "BLOCKED: No local APScheduler 3.x wheel found"
  echo "NEXT: Obtain approved APScheduler 3.x and dependency wheels"
else
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm -i --pull=never \
    --network=none --memory=12g --pids-limit=512 \
    -v "$PWD:/workspace:ro" \
    -v "$(dirname "$APSWHEEL"):/offline:ro" \
    -e 'PYTHONPATH=/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils' \
    -w /workspace \
    --entrypoint /bin/sh \
    localhost/cta-max-faiss:local -c '
      set -eu
      /opt/venv/bin/python -m pip install \
        --no-index --find-links=/offline \
        --target /tmp/pzaas-offline "APScheduler>=3,<4"
      export PYTHONPATH="/tmp/pzaas-offline:$PYTHONPATH"
      /opt/venv/bin/python -u - <<'"'"'PY'"'"'
import traceback

print("=== PZAAS NATIVE WORKER TEST ===", flush=True)
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    print("REAL APSCHEDULER: PASS", flush=True)

    from pzaas_native_serve_dev.pzaas_spawn_worker import PZAASFactoryWrapper
    pipeline = PZAASFactoryWrapper()()

    assert getattr(pipeline, "pzaas_native_adapter", None) is not None
    assert getattr(pipeline, "_pzaas_native_pipeline", False)

    print("NATIVE WORKER INITIALIZATION: PASS", flush=True)
    print("NEXT: BUILT-IN MAX SERVE HTTP 200", flush=True)
except Exception:
    print("NATIVE WORKER INITIALIZATION: BLOCKED", flush=True)
    traceback.print_exc()
    raise SystemExit(1)
finally:
    print("ORIGINAL DS / CTA / BPLAN: UNCHANGED BY TEST", flush=True)
PY
    '
fi
