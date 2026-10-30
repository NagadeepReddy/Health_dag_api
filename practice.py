python3 -B - <<'PY'
from pathlib import Path
import ast
import re
import os

pkg = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

helper = pkg / "cta_queue_compat.py"
scheduler = pkg / "cta_native_scheduler.py"

for p in (helper, scheduler):
    if not p.is_file() or p.is_symlink():
        raise SystemExit("STOP: Required isolated source unavailable: " + str(p))

source = helper.read_text()
tree = ast.parse(source)
scheduler_tree = ast.parse(scheduler.read_text())

# Confirm the scheduler exposes the actual CTA response types.
available = set()
for node in scheduler_tree.body:
    if isinstance(node, ast.ImportFrom):
        available.update(
            alias.asname or alias.name
            for alias in node.names
        )
    elif isinstance(node, ast.Import):
        available.update(
            alias.asname or alias.name.split(".")[0]
            for alias in node.names
        )
    elif isinstance(node, (ast.ClassDef, ast.FunctionDef)):
        available.add(node.name)

required = {
    "RequestID",
    "SchedulerResult",
    "CTASerializableOutput",
}

missing = required - available
if missing:
    raise SystemExit(
        "STOP: Scheduler response exports need review: "
        + ", ".join(sorted(missing))
    )

marker = "CTA_BATCH2_TYPED_RESPONSE_QUEUE_V1"

if marker in source:
    print("CTA RESPONSE QUEUE FIX: ALREADY PRESENT")
    raise SystemExit(0)

needle = "self.request_queue_config = ZmqConfig[Any](Any)"
if source.count(needle) != 1:
    raise SystemExit("STOP: Unexpected request queue compatibility source")

if "self.response_queue_config =" in source:
    raise SystemExit("STOP: Response queue already overridden; review required")

lines = source.splitlines(keepends=True)
matches = [
    i for i, line in enumerate(lines)
    if needle in line
]

if len(matches) != 1:
    raise SystemExit("STOP: Request queue assignment ambiguous")

index = matches[0]
indent = re.match(r"^\s*", lines[index]).group()

addition = [
    f"{indent}# {marker}\n",
    f"{indent}from maxserve_cta_extension import cta_native_scheduler as _cta_s\n",
    f"{indent}_cta_response_type = dict[\n",
    f"{indent}    _cta_s.RequestID,\n",
    f"{indent}    _cta_s.SchedulerResult[_cta_s.CTASerializableOutput],\n",
    f"{indent}]\n",
    f"{indent}self.response_queue_config = ZmqConfig[\n",
    f"{indent}    _cta_response_type\n",
    f"{indent}](_cta_response_type)\n",
]

updated = "".join(
    lines[:index + 1] + addition + lines[index + 1:]
)

ast.parse(updated)
compile(updated, str(helper), "exec")

backup = helper.with_name(
    "cta_queue_compat.py.before_response_fix.bak"
)
temp = helper.with_name(
    "cta_queue_compat.py.response_fix.tmp"
)

if backup.exists() or temp.exists():
    raise SystemExit("STOP: Backup or temporary file already exists")

with backup.open("x") as f:
    f.write(source)

try:
    with temp.open("x") as f:
        f.write(updated)
    os.replace(temp, helper)
finally:
    if temp.exists():
        temp.unlink()

ast.parse(helper.read_text())

print("CTA RESPONSE QUEUE TYPE: INSTALLED")
print("REQUEST QUEUE FIX: PRESERVED")
print("RESPONSE QUEUE SYNTAX: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
