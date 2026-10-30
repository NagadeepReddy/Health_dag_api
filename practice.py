timeout -s TERM -k 5s 75s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e OTEL_SDK_DISABLED=true \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max \
  0c95d4a8f887 \
  /opt/venv/bin/python -u -B - <<'PY'
print("PYTHON STARTUP: PASS", flush=True)

from maxserve_cta_extension.cta_queue_compat import install
assert install()
print("QUEUE COMPATIBILITY: PASS", flush=True)

from maxserve_cta_extension import cta_spawn_worker
print("WORKER IMPORT: PASS", flush=True)

print("BATCH-2 CONTAINER PREFLIGHT: PASS", flush=True)
PY
