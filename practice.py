podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --entrypoint /bin/grep \
  localhost/cta-max-faiss:local \
  -n -B 8 -A 12 \
  -E 'msgpack_numpy_decoder|_deserialize|payload_type' \
  /opt/venv/lib/python3.12/site-packages/max/serve/queue/zmq_queue.py
