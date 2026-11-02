python3 - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")
launcher = root / "bplan_native_launcher.py"
pipeline = root / "bplan_http_pipeline.py"

old = "BPlanNativeHTTPPipeline"
new = "BPLANNativeHTTPPipeline"

source = launcher.read_text()

assert source.count(old) == 2, f"STOP: found {source.count(old)} references, expected 2"
assert f"class {new}(" in pipeline.read_text(), "STOP: class not found"

updated = source.replace(old, new)
ast.parse(updated)
launcher.write_text(updated)

print("BPLAN CLASS NAME: FIXED (2 references)")
print("LAUNCHER SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
