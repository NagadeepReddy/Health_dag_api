python - <<'PY'
from pathlib import Path
import ast

b = Path("artifacts/v1.168-max/cta_max")
adapter = b / "context_head_base_max.py"
grec = b / "grecbase_max.py"

a = adapter.read_text()
g = grec.read_text()

old_a = "from context_head_full import ContextHeadFullMAX"
new_a = "from .context_head_full import ContextHeadFullMAX"

old_g = "from cta_max.context_head_full import ContextHeadFullMAX"
new_g = "from cta_max.context_head_base_max import ContextHeadBaseMAX"

assert a.count(old_a) == 1, "STOP: adapter import differs"
assert g.count(old_g) == 1, "STOP: GRecBase import differs"
assert g.count("ContextHeadFullMAX(") == 1, "STOP: constructor differs"

a2 = a.replace(old_a, new_a, 1)
g2 = g.replace(old_g, new_g, 1)
g2 = g2.replace("ContextHeadFullMAX(", "ContextHeadBaseMAX(", 1)

ast.parse(a2)
ast.parse(g2)

for p, old in [(adapter, a), (grec, g)]:
    backup = Path(str(p) + ".before_base_integration.bak")
    assert not backup.exists(), f"STOP: backup exists: {backup}"

for p, old, new in [(adapter, a, a2), (grec, g, g2)]:
    Path(str(p) + ".before_base_integration.bak").write_text(old)
    p.write_text(new)

print("BASE CONTEXTHEAD CONNECTED TO GRE CBASE")
print("SYNTAX OK")
print("TRANSFORMER AND ORIGINAL DS CODE UNCHANGED")
PY
