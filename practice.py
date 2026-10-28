timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c '
    FILE=/opt/venv/lib/python3.12/site-packages/max/serve/queue/zmq_queue.py
    echo "=== ZMQ CONFIGURATION AND ENDPOINTS ==="
    grep -n -A 95 -B 5 "class ZmqConfig" "$FILE" | head -110
    echo "=== SOCKET BIND / CONNECT ==="
    grep -n -E "bind\(|connect\(|class ZmqSocket|def __init__" "$FILE" | head -35
  '
