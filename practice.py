P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P cp cta-native-live:/opt/venv/lib/python3.12/site-packages/max/serve/queue/zmq_queue.py /tmp/cta_zmq_queue.py

sed -n '160,260p' /tmp/cta_zmq_queue.py
