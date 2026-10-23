cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

old = 'base.parent / "v1.168" / "core-artifact"'
new = 'base.parent.parent / "v1.168" / "core-artifact"'

assert s.count(old) == 1, "Expected path not found; no changes made"
assert Path("artifacts/v1.168/core-artifact/pipeline.py").is_file()

updated = s.replace(old, new)
compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA v1.168 DS PIPELINE PATH: FIXED")
print("SYNTAX: PASS")
PY
