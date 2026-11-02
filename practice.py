python3 - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")
launcher = root / "bplan_native_launcher.py"
pipeline = root / "bplan_http_pipeline.py"

source = launcher.read_text()
old = "BPlanNativeHTTPPipeline"
new = "BPLANNativeHTTPPipeline"

assert source.count(old) == 1, "STOP: unexpected launcher structure"
assert f"class {new}(" in pipeline.read_text(), "STOP: actual class not found"

updated = source.replace(old, new)
ast.parse(updated)
launcher.write_text(updated)

print("BPLAN HTTP CLASS IMPORT: FIXED")
print("LAUNCHER SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
