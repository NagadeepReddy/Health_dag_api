cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")
s = p.read_text()

old = "responses[request_id] = SchedulerResult.create(result)"
new = """responses[request_id] = SchedulerResult.create(
                    SimpleNamespace(is_done=True, result=result)
                )"""

assert s.count(old) == 1, "Unexpected scheduler code; no changes made"

updated = "from types import SimpleNamespace\n" + s.replace(old, new)

compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA REAL JSON RESULT WRAPPING: FIXED")
print("SYNTAX: PASS")
PY
