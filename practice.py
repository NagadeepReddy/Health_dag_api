python3 - <<'PY'
from pathlib import Path

p = Path("/tmp/cta_native_e2e_result.log")
lines = p.read_text(errors="replace").splitlines()

for i, line in enumerate(lines):
    if any(x in line for x in (
        "CTA_NATIVE_RESPONSE_TYPES",
        "CTA NATIVE HTTP STATUS",
        "CTA RESPONSE:",
        "Traceback (most recent call last)",
        "ValidationError",
        "RecursionError",
    )):
        print(f"\n=== LOG LINE {i+1} ===")
        print("\n".join(lines[i:min(i+28, len(lines))]))

print("\nLOG REVIEW COMPLETE")
PY
