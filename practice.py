cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

pattern = re.compile(r'^([ \t]*)async def wrapped\(\*args, \*\*kwargs\):', re.M)
matches = list(pattern.finditer(s))
assert len(matches) == 1, "Wrapper differs; no changes made"

indent = matches[0].group(1)
assert s.count("return await original(*bound.args, **bound.kwargs)") == 1, \
    "Original call differs; no changes made"

updated = pattern.sub(
    lambda m: (
        f"{indent}from contextlib import asynccontextmanager\n\n"
        f"{indent}@asynccontextmanager\n"
        f"{indent}async def wrapped(*args, **kwargs):"
    ),
    s,
    count=1
)

updated = updated.replace(
    "return await original(*bound.args, **bound.kwargs)",
    "async with original(*bound.args, **bound.kwargs) as monitor:\n"
    + indent + "        yield monitor",
    1
)

ast.parse(updated)

backup = p.with_name("cta_spawn_worker.py.before_context_fix")
if not backup.exists():
    backup.write_text(s)

p.write_text(updated)

print("NATIVE CTA ASYNC CONTEXT: FIXED")
print("SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY
