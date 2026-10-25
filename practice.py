cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

old = "        pipeline.cta_adapter = CTAMaxWorkerAdapter(CTA, attach_max)\n"
new = old + "        pipeline._cta_adapter = pipeline.cta_adapter\n"

if new in s:
    print("CTA ADAPTER ALIGNMENT: ALREADY DONE")
else:
    assert s.count(old) == 1, "Unexpected source; no changes made"
    updated = s.replace(old, new, 1)
    compile(updated, str(p), "exec")
    backup = p.with_name(p.name + ".before_adapter_alignment")
    assert not backup.exists(), "Backup already exists; no changes made"
    backup.write_text(s)
    p.write_text(updated)
    print("CTA ADAPTER ALIGNMENT: PASS")
    print("MAX-ONLY SYNTAX: PASS")
    print("ORIGINAL DS CODE: UNCHANGED")
PY
