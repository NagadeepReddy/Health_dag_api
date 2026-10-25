podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /bin/sh localhost/cta-max-faiss:local \
-c 'nl -ba /opt/venv/lib/python3.12/site-packages/max/serve/queue/zmq_queue.py | sed -n "160,195p;225,255p"'
