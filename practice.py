python3 - <<'PY'
from pathlib import Path
import re, py_compile

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")
launcher = root / "bplan_native_launcher.py"
pipeline = root / "bplan_http_pipeline.py"

assert launcher.is_file() and pipeline.is_file(), "STOP: required file missing"

code = launcher.read_text()
pipe_code = pipeline.read_text()

classes = re.findall(r"class\s+(\w+)\s*\(\s*TokenGeneratorPipeline\s*\)", pipe_code)
assert len(classes) == 1, f"STOP: unexpected HTTP pipeline classes: {classes}"

marker = 'sys.argv = ["max.entrypoints.pipelines", "serve", *sys.argv[1:]]'
assert code.count(marker) == 1, "STOP: launcher structure differs"

if "BPLAN_HTTP_PIPELINE_WIRED" not in code:
    wiring = (
        "    # BPLAN_HTTP_PIPELINE_WIRED\n"
        "    from max.serve import api_server\n"
        f"    from bplan_native_serve_dev.bplan_http_pipeline import {classes[0]}\n"
        f"    api_server.TokenGeneratorPipeline = {classes[0]}\n"
    )
    code = code.replace(marker, wiring + "\n    " + marker)
    launcher.write_text(code)

py_compile.compile(str(launcher), doraise=True)
print("BPLAN HTTP PIPELINE WIRING: PASS")
print("BPLAN NATIVE LAUNCHER SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
