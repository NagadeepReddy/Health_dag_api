cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py")
s = p.read_text()

old = "engine._cta_http_loop.call_soon_threadsafe(pending[rid].put_nowait, result[rid])"
new = """def deliver():
                    print("CTA CALLBACK EXECUTED", flush=True)
                    q = pending[rid]
                    q.put_nowait(result[rid])
                    print("CTA QUEUE SIZE AFTER PUT:", q.qsize(), flush=True)
                engine._cta_http_loop.call_soon_threadsafe(deliver)"""

assert s.count(old) == 1, "Bridge location not found or already modified"
s = s.replace(old, new)
compile(s, str(p), "exec")
p.write_text(s)
print("CTA CALLBACK TRACE: READY")
PY
