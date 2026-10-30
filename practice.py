podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -w /workspace -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max a176e284b50a /opt/venv/bin/python -B - <<'PY'
import ast
import inspect
import re
from pathlib import Path

pkg = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

print("=== CTA REQUEST AND QUEUE CONTRACT ===")

files = {
    "CTA CONTEXT": pkg / "cta_context.py",
    "CTA ROUTER": pkg / "cta_router.py",
    "CTA SCHEDULER FACTORY": pkg / "cta_scheduler_factory.py",
    "CTA HTTP PIPELINE": pkg / "cta_http_pipeline.py",
}

pattern = re.compile(
    r"serialize|deserialize|to_dict|from_dict|"
    r"CTAContext|queue\.stream|request_queue|"
    r"get_nowait|model_worker_queues|type|"
    r"CTASerializableOutput",
    re.I
)

for label, path in files.items():
    print("\n===", label, "===")
    if not path.is_file():
        print("NOT PRESENT:", path)
        continue

    lines = path.read_text().splitlines()
    ast.parse("\n".join(lines))

    matches = [
        i for i, line in enumerate(lines)
        if pattern.search(line)
    ]
    selected = set()

    for i in matches[:14]:
        selected.update(range(
            max(0, i - 2),
            min(len(lines), i + 4)
        ))

    for i in sorted(selected):
        print(f"{i+1}: {lines[i][:180]}")

print("\n=== INSTALLED MAX QUEUE SERIALIZER ===")

from max.serve.queue import zmq_queue
from max.interfaces.utils import serialization

for label, module in [
    ("MAX ZMQ QUEUE", zmq_queue),
    ("MAX SERIALIZATION", serialization),
]:
    print("\n===", label, "===")
    src = inspect.getsource(module).splitlines()

    matches = [
        i for i, line in enumerate(src)
        if re.search(
            r"def get_nowait|def put_nowait|"
            r"_deserialize|_serialize|"
            r"Decoder\(|msgspec|tag_field|"
            r"RequestType|type=",
            line
        )
    ]

    selected = set()
    for i in matches[:18]:
        selected.update(range(
            max(0, i - 2),
            min(len(src), i + 4)
        ))

    for i in sorted(selected):
        print(f"{i+1}: {src[i][:180]}")

print("\nQUEUE CONTRACT INSPECTION: COMPLETE")
print("MODEL EXECUTIONS: ZERO")
print("SOURCE CHANGES: NONE")
print("CONTAINERS RESTARTED: NONE")
PY
