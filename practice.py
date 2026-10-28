cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -B - <<'PY'
from pathlib import Path
import ast
import shutil

root = Path("artifacts/v1.168-max/maxserve_cta_extension")
source = (root / "cta_native_e2e_test.py").read_text()
target = root / "cta_spawn_safe_probe.py"
original = target.read_text()

marker = "# CTA-only native queue compatibility."
anchor = "from types import SimpleNamespace"

assert marker in source
assert anchor in source
assert "import json" in original
assert shutil.disk_usage("/application1").free > 10 * 1024 * 1024

patch = source.split(anchor, 1)[0]
assert "_cta_queues.SchedulerZmqConfigs.__init__ = _cta_queue_init" in patch
assert "response_queue_config" in patch

if marker in original:
    print("QUEUE FIX: ALREADY PRESENT")
else:
    updated = patch + "\n" + original
    ast.parse(updated)
    backup = target.with_suffix(".py.pre_queue_fix.bak")
    assert not backup.exists(), "Backup already exists; no changes made"
    shutil.copy2(target, backup)
    target.write_text(updated)
    print("CTA QUEUE COMPATIBILITY: APPLIED")

ast.parse(target.read_text())
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY
