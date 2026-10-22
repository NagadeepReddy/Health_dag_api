timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=4g --pids-limit=32 \
  --entrypoint /bin/sh \
  f30453065dac \
  -c 'grep -Rnl --include="*.py" "start_model_worker(" /opt/venv/lib/python3.12/site-packages/max/serve | head -15'
