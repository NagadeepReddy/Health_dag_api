podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c "grep -R -n -C 5 -E 'MsgpackNumpy|msgspec|enc_hook|dec_hook|encode\\(|decode\\(' \
  /opt/venv/lib/python3.12/site-packages/max/serve/scheduler/queues.py \
  /opt/venv/lib/python3.12/site-packages/max/interfaces/utils/serialization.py | head -130"
