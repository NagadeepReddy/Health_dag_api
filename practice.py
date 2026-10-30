timeout -s TERM -k 5s 75s \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
exec -i \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max \
a176e284b50a \
/opt/venv/bin/python -u -B - <<'PY'
print("PYTHON STARTUP: PASS", flush=True)

from max.serve.scheduler.queues import SchedulerZmqConfigs
print("MAX QUEUE IMPORT: PASS", flush=True)

from maxserve_cta_extension.cta_queue_compat import install
assert install()
assert SchedulerZmqConfigs._cta_batch2_queue_compat
print("BATCH-2 QUEUE COMPATIBILITY: PASS", flush=True)

from maxserve_cta_extension import cta_spawn_worker
print("NATIVE WORKER IMPORT: PASS", flush=True)

print("STARTUP VERIFICATION: COMPLETE", flush=True)
print("MODEL EXECUTIONS: ZERO", flush=True)
PY
