cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout 15s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -i --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --tmpfs /tmp:rw,size=16m,mode=1777 \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -B - <<'PY'
import zmq

ctx = zmq.Context()
push = ctx.socket(zmq.PUSH)
pull = ctx.socket(zmq.PULL)

try:
    endpoint = "ipc:///tmp/cta-transport-test.sock"
    push.bind(endpoint)
    pull.connect(endpoint)

    push.send_string("cta-test")
    if pull.poll(3000):
        assert pull.recv_string() == "cta-test"
        print("ZMQ IPC TRANSPORT: PASS", flush=True)
    else:
        print("ZMQ IPC TRANSPORT: FAIL", flush=True)
finally:
    push.close(linger=0)
    pull.close(linger=0)
    ctx.term()

print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
echo "TEST EXIT CODE: $?"
