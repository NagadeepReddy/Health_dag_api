cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout 20s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=4g --pids-limit=32 \
  --entrypoint /bin/sh \
  f30453065dac \
  -c 'sed -n "1,130p" /opt/venv/lib/python3.12/site-packages/max/serve/router/kserve_routes.py'
