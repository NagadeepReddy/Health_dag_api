cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
original = p.read_text()
lines = original.splitlines(keepends=True)

fixes = [
    (r"pipeline\.cta_adapter\s*=\s*CTAMaxWorkerAdapter\(CTA,\s*attach_max\)",
     "pipeline._cta_adapter = pipeline.cta_adapter"),
    (r"pipeline\.cta_native_pipeline\s*=\s*True",
     "pipeline._cta_native_pipeline = True"),
]

for pattern, new_line in fixes:
    if any(line.strip() == new_line for line in lines):
        continue

    matches = [i for i, line in enumerate(lines)
               if re.fullmatch(pattern, line.strip())]
    assert len(matches) == 1, f"Unexpected source for {new_line}"

    i = matches[0]
    indent = re.match(r"[ \t]*", lines[i]).group()
    lines[i] += indent + new_line + "\n"

updated = "".join(lines)
compile(updated, str(p), "exec")

if updated != original:
    backup = p.with_name(p.name + ".before_native_flag_alignment")
    assert not backup.exists(), "Backup exists; no changes made"
    backup.write_text(original)
    p.write_text(updated)

print("CTA ADAPTER AND PIPELINE FLAGS: PASS")
print("MAX SYNTAX: PASS")
print("DS FILES: UNCHANGED")
PY
