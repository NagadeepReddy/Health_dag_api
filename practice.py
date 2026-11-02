python3 - <<'PY'
from pathlib import Path
import py_compile

d = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")

files = {
    "launcher": d / "bplan_native_launcher.py",
    "worker": d / "bplan_spawn_worker.py",
    "scheduler": d / "bplan_native_scheduler.py",
}

for name, path in files.items():
    assert path.is_file(), f"STOP: missing {path}"

assert "class BPlanSerializableOutput" in files["scheduler"].read_text(), \
    "STOP: BPLAN response class not confirmed"

compat = d / "bplan_queue_compat.py"
compat.write_text('''"""BPLAN-only typed MAX Serve response queue compatibility."""

def install():
    from max.serve.scheduler.queues import SchedulerZmqConfigs
    from max.serve.queue.zmq_queue import ZmqConfig
    from max.interfaces.request import RequestID
    from max.interfaces.scheduler import SchedulerResult
    from bplan_native_serve_dev.bplan_native_scheduler import BPlanSerializableOutput

    if getattr(SchedulerZmqConfigs, "_bplan_typed_response", False):
        return False

    response_type = dict[RequestID, SchedulerResult[BPlanSerializableOutput]]
    original_init = SchedulerZmqConfigs.__init__

    def bplan_queue_init(self, pipeline_task):
        original_init(self, pipeline_task)
        self.response_queue_config = ZmqConfig[response_type](response_type)

    SchedulerZmqConfigs.__init__ = bplan_queue_init
    SchedulerZmqConfigs._bplan_typed_response = True
    print("BPLAN TYPED MAX RESPONSE QUEUE: INSTALLED", flush=True)
    return True
''')

patches = [
    (files["launcher"], "def main():"),
    (files["worker"], "    def __call__(self):"),
]

marker = "# BPLAN_TYPED_RESPONSE_QUEUE_V1"

for path, anchor in patches:
    source = path.read_text()
    if marker in source:
        print(path.name, "ALREADY PATCHED")
        continue

    assert source.count(anchor) == 1, f"STOP: unexpected structure in {path.name}"

    indent = "    " if path == files["launcher"] else "        "
    addition = (
        "\n" + indent + marker +
        "\n" + indent +
        "from bplan_native_serve_dev.bplan_queue_compat import install" +
        "\n" + indent + "install()" + "\n"
    )

    path.with_suffix(".py.pre_typed_queue_backup").write_text(source)
    path.write_text(source.replace(anchor, anchor + addition, 1))

for path in [compat, *files.values()]:
    py_compile.compile(str(path), doraise=True)

print("BPLAN TYPED RESPONSE PATCH: PASS")
print("BPLAN SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
