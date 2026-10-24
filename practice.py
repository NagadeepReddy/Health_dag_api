cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
old = 'base.parent.parent / "v1.168" / "core-artifact"'
new = 'base.parent / "v1.168" / "core-artifact"'

assert Path("artifacts/v1.168/core-artifact/pipeline.py").is_file(), "Original pipeline.py not found"
s = p.read_text()
assert old in s, "Expected path not found; no changes made"

p.write_text(s.replace(old, new, 1))
compile(p.read_text(), str(p), "exec")
print("CTA PIPELINE PATH FIXED — Syntax PASS")
PY
