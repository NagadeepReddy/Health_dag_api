cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

old1 = "        pipeline = self.original_factory()\n"
old2 = "        pipeline.cta_adapter = CTAWorkerAdapter(CTA, attach_max)\n"

assert s.count(old1) == 1, "Factory code differs; no changes made"
assert s.count(old2) == 1, "Adapter code differs; no changes made"

updated = s.replace(old1, "", 1)
updated = updated.replace(
    old2,
    "        pipeline = CTA()\n" + old2,
    1
)

ast.parse(updated)
backup = p.with_suffix(".py.before_cta_factory_fix")
if not backup.exists():
    backup.write_text(s)
p.write_text(updated)

print("CTA REAL FACTORY: FIXED")
print("SYNTAX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
