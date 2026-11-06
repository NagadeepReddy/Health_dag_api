
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import re

stage = Path("/application1/sajjna8/max_shared_infra/isolated/pzaas_shared_wiring_v1")
target = stage / "pzaas_spawn_worker.py"
adapter = stage / "pzaas_max_model_adapter.py"

print("=== ISOLATED SHARED MAX WORKER CORRECTION ===")

if not target.is_file():
    raise SystemExit("STOP: Isolated worker startup file missing")

source = target.read_text()

if adapter.is_file():
    adapter_source = adapter.read_text()
else:
    adapter_path = Path("/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106/model/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_max_model_adapter.py")
    if not adapter_path.is_file():
        raise SystemExit("STOP: Original worker adapter missing")
    adapter_source = adapter_path.read_text()

if not re.search(r"def initialize\s*\(self\)", adapter_source):
    raise SystemExit("STOP: Original initialize method not verified")

pattern = re.compile(
    r"(?ms)^([ \t]*)lifecycle\s*=\s*WorkerLifecycle\(\n"
    r".*?^\1worker\.pipeline\s*=\s*pipeline[ \t]*$"
)
matches = list(pattern.finditer(source))

if len(matches) != 1:
    raise SystemExit(
        f"STOP: Expected one shared lifecycle block; found {len(matches)}"
    )

match = matches[0]
old = match.group(0)

if not all(term in old for term in (
    "worker.pipeline_factory",
    "worker.attach_max",
    "lifecycle.start()",
)):
    raise SystemExit("STOP: Unexpected lifecycle structure; no changes made")

indent = match.group(1)
replacement = "\n".join([
    indent + "lifecycle = WorkerLifecycle(",
    indent + "    create=worker.initialize,",
    indent + "    load=lambda pipeline: None,",
    indent + "    attach_max=lambda pipeline: None,",
    indent + ")",
    indent + "pipeline = lifecycle.start()",
    indent + "worker.pipeline = pipeline",
])

updated = source[:match.start()] + replacement + source[match.end():]
compile(updated, str(target), "exec")

target.write_text(updated)

print("ORIGINAL WORKER INITIALIZATION: RESTORED THROUGH SHARED LIFECYCLE")
print("SHARED WORKER LIFECYCLE: RETAINED")
print("ISOLATED PYTHON SYNTAX: PASS")
print("ORIGINAL PZAAS HANDOFF: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NO CONTAINERS STARTED")
print("NEXT: VERIFY CORRECTED ISOLATED WORKER STARTUP")
PY
