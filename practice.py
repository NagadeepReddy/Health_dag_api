python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev/bplan_native_worker_adapter.py")
s = p.read_text()

old = """            class MAXProxy:
                def __call__(self, **kwargs):
                    self.max_calls += 1
                    return backend(**kwargs)"""

new = """            owner = self

            class MAXProxy:
                def __call__(self, **kwargs):
                    owner.max_calls += 1
                    print("BPLAN REAL MAX EXECUTION START:", owner.max_calls, flush=True)
                    result = backend(**kwargs)
                    print("BPLAN REAL MAX EXECUTION PASS", flush=True)
                    return result"""

if old in s:
    p.write_text(s.replace(old, new, 1))
    print("BPLAN MAX COUNTER FIX: APPLIED")
elif "BPLAN REAL MAX EXECUTION START:" in s:
    print("BPLAN MAX COUNTER FIX: ALREADY PRESENT")
else:
    raise SystemExit("STOP: Expected code not found; no changes made")

py_compile.compile(str(p), doraise=True)
print("BPLAN SYNTAX: PASS")
PY
