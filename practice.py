cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
test = base / "cta_native_e2e_test.py"
sched = base / "cta_native_scheduler.py"

updates = {}

for p in (test, sched):
    s = p.read_text()

    # Remove only incorrectly positioned imports inserted previously.
    s = re.sub(
        r'(?m)^from max\.interfaces\.request import RequestID\n(?=[ \t]+from max\.interfaces\.scheduler import)',
        '',
        s
    )

    # Insert RequestID import at the SAME indentation as SchedulerResult.
    if "from max.interfaces.request import RequestID" not in s:
        match = re.search(
            r'(?m)^([ \t]*)from max\.interfaces\.scheduler import ',
            s
        )
        assert match, f"Scheduler import not found: {p.name}"
        indent = match.group(1)
        s = (
            s[:match.start()]
            + indent + "from max.interfaces.request import RequestID\n"
            + s[match.start():]
        )

    if p == test:
        s = s.replace(
            "dict[str, SchedulerResult[CTASerializableOutput]]",
            "dict[RequestID, SchedulerResult[CTASerializableOutput]]"
        )
    else:
        s = s.replace(
            "responses[request_id] = SchedulerResult.create(",
            "responses[RequestID(request_id)] = SchedulerResult.create("
        )

    compile(s, str(p), "exec")
    updates[p] = s

# Write only if BOTH files pass syntax validation.
for p, s in updates.items():
    p.write_text(s)

print("CTA IMPORT INDENTATION: PASS")
print("CTA RESPONSE-ID ALIGNMENT: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
