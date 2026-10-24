cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()

marker = re.search(r"(?m)^([ \t]*)register_cta_routes\(\)[ \t]*$", s)
assert marker, "CTA route registration point not found"

hook = (
    "from max.serve import api_server\n"
    "from maxserve_cta_extension.cta_http_pipeline import CTANativeHTTPPipeline\n"
    "api_server.TokenGeneratorPipeline = CTANativeHTTPPipeline"
)

if "api_server.TokenGeneratorPipeline = CTANativeHTTPPipeline" not in s:
    indent = marker.group(1)
    insertion = "\n".join(indent + line for line in hook.splitlines())
    pos = marker.end()
    s = s[:pos] + "\n" + insertion + s[pos:]
    py_compile.compile(str(p), doraise=True)
    p.write_text(s)

print("CTA MAX BUILT-IN PIPELINE HOOK: SYNTAX PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
