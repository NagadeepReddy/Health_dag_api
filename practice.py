cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=4g --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  f30453065dac \
  -u -c '
from types import SimpleNamespace
from max.interfaces.scheduler import SchedulerResult
from maxserve_cta_extension.cta_native_scheduler import CTANativeScheduler

output = SimpleNamespace(is_done=True, result=None)
wrapped = SchedulerResult.create(output)

assert wrapped is not None
assert callable(CTANativeScheduler.run_iteration)
print("NATIVE CTA RESULT CONTRACT: PASS", flush=True)
'

echo "EXIT CODE: $?"
