python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_queue_compat.py")

s = p.read_text()
old = "        original_init(self, pipeline_task)\n        self.response_queue_config"
new = (
    "        original_init(self, pipeline_task)\n"
    "        from typing import Any\n"
    "        self.request_queue_config = ZmqConfig[Any](Any)\n"
    "        self.response_queue_config"
)

if "self.request_queue_config = ZmqConfig[Any](Any)" in s:
    print("REQUEST QUEUE FIX: ALREADY PRESENT")
elif s.count(old) == 1:
    p.write_text(s.replace(old, new, 1))
    print("REQUEST QUEUE FIX: APPLIED")
else:
    raise SystemExit("STOP: Expected insertion point not found; no changes made")

py_compile.compile(str(p), doraise=True)
print("BPLAN SYNTAX: PASS")
for i, line in enumerate(p.read_text().splitlines(), 1):
    if 13 <= i <= 25:
        print(f"{i}: {line}")
PY
