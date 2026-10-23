timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=4g --pids-limit=32 \
  --entrypoint /opt/venv/bin/python \
  f30453065dac \
  -u -c '
from max.interfaces.scheduler import SchedulerResult

sample = {"offers": [{"id": "test"}]}
result = SchedulerResult.create(sample)

print("NATIVE CTA JSON RESULT: PASS", flush=True)
print("RESULT TYPE:", type(result).__name__, flush=True)
'

echo "EXIT CODE: $?"
