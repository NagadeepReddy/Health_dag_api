cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
router = base / "cta_router.py"
scheduler = base / "cta_native_scheduler.py"

r = router.read_text()
s = scheduler.read_text()

old = "queue.open_channel(request_id, context)"
new = 'queue.open_channel(request_id, {"request_id": request_id, "body": body})'

if old not in r:
    raise SystemExit("Router pattern differs; no files changed")

pattern = r"(?m)^([ \t]*)request_id = context\.request_id\b"
match = re.search(pattern, s)

if not match:
    raise SystemExit("Scheduler pattern differs; no files changed")

indent = match.group(1)
replacement = (
    indent + "if isinstance(context, dict):\n"
    + indent + "    from .cta_context import CTAContext\n"
    + indent + '    context = CTAContext(context["request_id"], context["body"])\n'
    + indent + "request_id = context.request_id"
)

r_new = r.replace(old, new, 1)
s_new = re.sub(pattern, lambda m: replacement, s, count=1)

compile(r_new, str(router), "exec")
compile(s_new, str(scheduler), "exec")

for path, original, updated in (
    (router, r, r_new),
    (scheduler, s, s_new),
):
    path.with_suffix(".before_queue_fix.bak").write_text(original)
    path.write_text(updated)

print("JSON queue transport FIXED")
print("Scheduler context reconstruction FIXED")
print("Syntax PASS")
PY
