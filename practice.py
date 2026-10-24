cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")
s = p.read_text()

if "CTA MAX REQUEST UNWRAPPED" not in s:
    matches = list(re.finditer(
        r'(?m)^([ \t]*)if isinstance\(context, dict\):[ \t]*$',
        s
    ))
    assert len(matches) == 1, "Expected conversion block not found"

    m = matches[0]
    i = m.group(1)

    fix = (
        f'{i}if isinstance(context, dict) and "body" not in context:\n'
        f'{i}    if len(context) != 1:\n'
        f'{i}        raise RuntimeError("CTA batching not yet supported")\n'
        f'{i}    queued_id, context = next(iter(context.items()))\n'
        f'{i}    print("CTA MAX REQUEST UNWRAPPED:", queued_id, flush=True)\n'
    )

    s = s[:m.start()] + fix + s[m.start():]
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA MAX QUEUE FORMAT FIX: INSTALLED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
