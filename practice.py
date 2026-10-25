cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py")
s = p.read_text()

old = "engine._cta_http_loop.call_soon_threadsafe(pending[rid].put_nowait, result[rid])"

new = """engine._cta_http_loop.call_soon_threadsafe(
                    lambda q=pending[rid], item=result[rid]: (
                        print("CTA CALLBACK EXECUTED", flush=True),
                        q.put_nowait(item),
                        print("CTA QUEUE SIZE:", q.qsize(), flush=True)
                    )
                )"""

assert s.count(old) == 1, "Expected original bridge not found"

s = s.replace(old, new, 1)
compile(s, str(p), "exec")
p.write_text(s)

print("CTA CALLBACK TRACE: SYNTAX PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
