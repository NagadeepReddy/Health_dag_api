cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()

old = "from max.serve.pipelines import TokenGeneratorPipeline"
new = "from max.serve.api_server import TokenGeneratorPipeline"

assert old in s, "Expected import not found"
p.write_text(s.replace(old, new, 1))

py_compile.compile(str(p), doraise=True)

print("CTA HTTP PIPELINE IMPORT FIX: SYNTAX PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
