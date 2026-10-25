cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path
p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()
lines = s.splitlines(keepends=True)
matches = [i for i, line in enumerate(lines) if "wrapped._cta_native_pipeline = True" in line]
assert len(matches) == 1, "Expected exactly one flag assignment"
i = matches[0]
indent = lines[i-1][:len(lines[i-1]) - len(lines[i-1].lstrip())]
lines[i] = indent + "wrapped._cta_native_pipeline = True\n"
p.write_text("".join(lines))
compile(p.read_text(), str(p), "exec")
print("INDENTATION FIX: PASS")
PY
