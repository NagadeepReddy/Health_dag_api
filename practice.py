podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.interfaces.scheduler import SchedulerResult; print(inspect.getsource(SchedulerResult.create)); print("FIELDS:", SchedulerResult.__annotations__)'
