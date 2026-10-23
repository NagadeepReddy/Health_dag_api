cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

old = '''            async for output in queue.open_channel(request_id, context):
                if output is None:
                    continue
                result = getattr(output, "result", None)
                if result is None:
                    continue
                if isinstance(result, dict) and "error" in result:
                    raise HTTPException(500, detail=result)
                return result'''

new = '''            with queue.open_channel(request_id, context) as response_queue:
                while True:
                    output = await response_queue.get()
                    if output is None:
                        continue
                    result = getattr(output, "result", None)
                    if result is None:
                        continue
                    if isinstance(result, dict) and "error" in result:
                        raise HTTPException(500, detail=result)
                    return result'''

if old in s:
    updated = s.replace(old, new, 1)
    compile(updated, str(p), "exec")
    p.with_name(p.name + ".before_response_fix.bak").write_text(s)
    p.write_text(updated)
    print("Native response handling FIXED")
elif new in s:
    print("Already fixed")
else:
    print("Code differs; no changes made")

py_compile.compile(str(p), doraise=True)
print("Syntax PASS")
PY
