cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 35s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=4g --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  f30453065dac \
  -u -c '
from maxserve_cta_extension.cta_native_scheduler import CTANativeScheduler
from max.interfaces.scheduler import SchedulerResult

assert callable(SchedulerResult.create)
assert callable(CTANativeScheduler.run_iteration)

print("REAL MAX CTA SCHEDULER IMPORT: PASS", flush=True)
print("MAX RESULT INTERFACE: PASS", flush=True)
'

echo "EXIT CODE: $?"
