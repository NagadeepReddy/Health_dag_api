cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py")
s = p.read_text()
marker = "    import uvicorn\n"

trace = '''    # CTA LIVE HANDOFF TRACE
    from max.serve.queue.zmq_queue import ZmqPullSocket
    original_receive = ZmqPullSocket.get_nowait

    def trace_receive(sock):
        result = original_receive(sock)
        if isinstance(result, dict) and result:
            pipeline = getattr(app.state, "pipeline", None)
            engine = getattr(pipeline, "_engine_queue", None)
            pending = getattr(engine, "pending_out_queues", {})
            for rid in result:
                print("LIVE RESPONSE ID:", repr(rid), flush=True)
                print("LIVE PENDING IDS:", list(pending), flush=True)
                print("LIVE DISPATCH MATCH:", rid in pending, flush=True)
        return result

    ZmqPullSocket.get_nowait = trace_receive
'''

if "CTA LIVE HANDOFF TRACE" not in s:
    assert marker in s, "Live-server insertion point missing"
    s = s.replace(marker, trace + marker, 1)

compile(s, str(p), "exec")
p.write_text(s)
print("CTA LIVE RESPONSE TRACE: READY")
print("ORIGINAL DS CODE: UNCHANGED")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage stop cta-native-live

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -d --rm --name cta-native-live \
  --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py
