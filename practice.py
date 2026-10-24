cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")
s = p.read_text()

anchor = "context = self.drainer.retrieve_item()"
marker = "CTA REQUEST RECEIVED:"

if marker not in s:
    assert s.count(anchor) == 1, "Expected scheduler location missing"
    s = s.replace(
        anchor,
        anchor + '\n                print("CTA REQUEST RECEIVED:", type(context).__name__, flush=True)',
        1
    )
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA REQUEST TRACE: READY")
print("DS CODE: UNCHANGED")
PY
