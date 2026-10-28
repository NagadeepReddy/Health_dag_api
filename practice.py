timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c '
    echo "=== ZMQ SOCKET CONNECTION LOGIC ==="
    nl -ba /opt/venv/lib/python3.12/site-packages/max/serve/queue/zmq_queue.py \
      | sed -n "100,155p"
  '
