python3 -B - <<'PY'
from pathlib import Path
import ast
import os
import subprocess
from typing import Any

root = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max"
)
pkg = (
    root / "cta_native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

launcher = pkg / "cta_native_launcher.py"
worker = pkg / "cta_spawn_worker.py"
helper = pkg / "cta_queue_compat.py"

for p in (launcher, worker):
    if not p.is_file() or p.is_symlink():
        raise SystemExit("STOP: Required isolated file unavailable")

marker = "CTA_BATCH2_QUEUE_COMPAT_V1"

helper_code = '''"""Isolated CTA native MAX queue compatibility."""
from typing import Any

def install():
    from max.serve.scheduler.queues import SchedulerZmqConfigs
    from max.serve.queue.zmq_queue import ZmqConfig
    from max.serve.config import Settings, APIType

    if not getattr(
        SchedulerZmqConfigs,
        "_cta_batch2_queue_compat",
        False,
    ):
        original_queue_init = SchedulerZmqConfigs.__init__

        def cta_queue_init(self, pipeline_task):
            original_queue_init(self, pipeline_task)
            self.request_queue_config = ZmqConfig[Any](Any)

        SchedulerZmqConfigs.__init__ = cta_queue_init
        SchedulerZmqConfigs._cta_batch2_queue_compat = True

    if not getattr(Settings, "_cta_batch2_kserve", False):
        original_settings_init = Settings.__init__

        def cta_settings_init(self, *args, **kwargs):
            original_settings_init(self, *args, **kwargs)
            if APIType.KSERVE not in self.api_types:
                self.api_types = list(self.api_types) + [
                    APIType.KSERVE
                ]

        Settings.__init__ = cta_settings_init
        Settings._cta_batch2_kserve = True

    return True
'''

launcher_text = launcher.read_text()
worker_text = worker.read_text()

ast.parse(helper_code)
launcher_tree = ast.parse(launcher_text)
worker_tree = ast.parse(worker_text)

main = [
    n for n in launcher_tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "main"
]

if len(main) != 1 or not main[0].body:
    raise SystemExit("STOP: Unexpected launcher structure")

launcher_install = (
    "    # CTA_BATCH2_QUEUE_COMPAT_V1\n"
    "    from maxserve_cta_extension.cta_queue_compat "
    "import install as _cta_queue_install\n"
    "    _cta_queue_install()\n"
)

worker_install = (
    "# CTA_BATCH2_QUEUE_COMPAT_V1\n"
    "from maxserve_cta_extension.cta_queue_compat "
    "import install as _cta_queue_install\n"
    "_cta_queue_install()\n"
)

def stage_launcher(source):
    if marker in source:
        return source

    lines = source.splitlines(keepends=True)
    index = main[0].body[0].lineno - 1
    lines.insert(index, launcher_install)
    return "".join(lines)

def stage_worker(source):
    if marker in source:
        return source

    lines = source.splitlines(keepends=True)
    index = 0

    body = worker_tree.body

    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        index = body[0].end_lineno

    for node in body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
        ):
            index = max(index, node.end_lineno)

    lines.insert(index, "\n" + worker_install + "\n")
    return "".join(lines)

new_launcher = stage_launcher(launcher_text)
new_worker = stage_worker(worker_text)

for p, text in (
    (launcher, new_launcher),
    (worker, new_worker),
    (helper, helper_code),
):
    ast.parse(text)
    compile(text, str(p), "exec")

if helper.exists():
    if helper.is_symlink() or helper.read_text() != helper_code:
        raise SystemExit("STOP: Existing helper differs")

for p, text, original in (
    (launcher, new_launcher, launcher_text),
    (worker, new_worker, worker_text),
):
    if text == original:
        continue

    backup = p.with_name(p.name + ".pre_queue_compat.bak")
    if backup.exists():
        raise SystemExit("STOP: Existing backup " + str(backup))

# All syntax/structure checks passed before writing.
if not helper.exists():
    with helper.open("x") as f:
        f.write(helper_code)

for p, text, original in (
    (launcher, new_launcher, launcher_text),
    (worker, new_worker, worker_text),
):
    if text == original:
        print(p.name, "ALREADY PATCHED")
        continue

    backup = p.with_name(p.name + ".pre_queue_compat.bak")
    temp = p.with_name(p.name + ".queue_compat.tmp")

    with backup.open("x") as f:
        f.write(original)

    if temp.exists():
        raise SystemExit("STOP: Temporary file already exists")

    try:
        with temp.open("x") as f:
            f.write(text)
        os.replace(temp, p)
    finally:
        if temp.exists():
            temp.unlink()

    print(p.name, "QUEUE COMPATIBILITY INSTALLED")

for p in (launcher, worker, helper):
    ast.parse(p.read_text())

print("ISOLATED SOURCE SYNTAX: PASS")

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
]

ids = subprocess.check_output(
    P + ["ps", "-q"], text=True
).split()

matches = [x for x in ids if x.startswith("a176e284b50a")]

if len(matches) != 1:
    raise SystemExit("STOP: Existing development container unavailable")

preflight = r'''
from typing import Any
from max.serve.scheduler.queues import SchedulerZmqConfigs
from max.serve.config import Settings, APIType
from maxserve_cta_extension.cta_queue_compat import install

assert install()
assert SchedulerZmqConfigs._cta_batch2_queue_compat
assert APIType.KSERVE in Settings().api_types

from maxserve_cta_extension import cta_spawn_worker

assert SchedulerZmqConfigs._cta_batch2_queue_compat

print("REQUEST QUEUE COMPATIBILITY: PASS")
print("KSERVE CONFIGURATION: PASS")
print("SPAWN WORKER IMPORT: PASS")
print("RESPONSE/CANCEL QUEUE LOGIC: UNCHANGED")
'''

environment = (
    "/workspace/artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate:"
    "/workspace/artifacts/v1.168/core-artifact:"
    "/batch2:"
    "/workspace/artifacts/v1.168-max"
)

result = subprocess.run(
    P + [
        "exec", "-i", "-w", "/workspace",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "PYTHONPATH=" + environment,
        matches[0],
        "/opt/venv/bin/python", "-B", "-",
    ],
    input=preflight,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    timeout=45,
)

print(result.stdout[-3500:])
print("PREFLIGHT EXIT CODE:", result.returncode)
print("ORIGINAL DS/MAX: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")

if result.returncode:
    raise SystemExit(1)
PY
