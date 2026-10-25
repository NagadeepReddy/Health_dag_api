podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-native-live sh -c \
  "grep -nE 'class .*Queue|response_worker|pending_out_queues|create_task|def .*receive|def .*dispatch|def open_channel' /opt/venv/lib/python3.12/site-packages/max/serve/queue/zmq_queue.py"
