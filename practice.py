podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.interfaces.queue import BackgroundQueueDrainer

print("=== MAX BACKGROUND REQUEST RECEIVER ===")
print(inspect.getsource(BackgroundQueueDrainer._drain_queue_background))
print("RECEIVER REVIEW COMPLETE")
PY
