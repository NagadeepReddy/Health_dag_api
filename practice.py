timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=4g --pids-limit=32 \
  --entrypoint /bin/sh \
  f30453065dac \
  -c 'grep -Rn -A 12 -B 3 "PipelineOutputType" /opt/venv/lib/python3.12/site-packages/max/interfaces --include="*.py" | head -85'
