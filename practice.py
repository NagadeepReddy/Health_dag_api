timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c '
    echo "=== RESPONSE SOCKET SEND/RECEIVE ==="
    grep -n -A 45 -B 5 -E "class ZmqPushSocket|class ZmqPullSocket|def put_nowait|def get_nowait" \
      /opt/venv/lib/python3.12/site-packages/max/serve/queue/zmq_queue.py | head -150

    echo "=== WORKER QUEUE CONFIGURATION ==="
    grep -n -A 45 -B 5 "def model_worker_queues" \
      /opt/venv/lib/python3.12/site-packages/max/serve/scheduler/queues.py
  '
