cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -B - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_http_entry.py")
s = p.read_text()

import_anchor = "from maxserve_cta_extension.cta_router import register_cta_routes\n"
new_import = "from maxserve_cta_extension.cta_http_pipeline import CTANativeHTTPPipeline\n"

hook_anchor = "    register_cta_routes()\n"
new_hook = "    api_server.TokenGeneratorPipeline = CTANativeHTTPPipeline\n"

if new_import not in s:
    assert s.count(import_anchor) == 1, "STOP: import location changed"
    s = s.replace(import_anchor, import_anchor + new_import)

if new_hook not in s:
    assert s.count(hook_anchor) == 1, "STOP: hook location changed"
    s = s.replace(hook_anchor, hook_anchor + new_hook)

ast.parse(s)

tmp = p.with_name(p.name + ".new")
tmp.write_text(s)
tmp.replace(p)

print("CTA NATIVE HTTP PIPELINE WIRING: FIXED")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY
