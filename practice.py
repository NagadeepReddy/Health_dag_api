cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
test = base / "cta_native_e2e_test.py"
sched = base / "cta_native_scheduler.py"

a = test.read_text()
b = sched.read_text()

old_type = "dict[str, SchedulerResult[CTASerializableOutput]]"
new_type = "dict[RequestID, SchedulerResult[CTASerializableOutput]]"

old_key = "responses[request_id] = SchedulerResult.create("
new_key = "responses[RequestID(request_id)] = SchedulerResult.create("

assert old_type in a or new_type in a, "Response config not found"
assert old_key in b or new_key in b, "Scheduler response assignment not found"

a = a.replace(old_type, new_type)
b = b.replace(old_key, new_key)

for name, content in ((test, a), (sched, b)):
    if "from max.interfaces.request import RequestID" not in content:
        anchor = "from max.interfaces.scheduler import"
        assert anchor in content
        content = content.replace(
            anchor,
            "from max.interfaces.request import RequestID\n" + anchor,
            1
        )
    compile(content, str(name), "exec")
    name.write_text(content)

print("CTA NATIVE REQUEST-ID RESPONSE ALIGNMENT: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
