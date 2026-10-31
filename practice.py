python3 -B - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
release = root / "cta_native_batch2_release_candidate"
backend = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py")

assert release.is_dir(), "STOP: Release missing"
assert backend.is_file(), "STOP: Validated backend missing"

print("=== RELEASE REUSABILITY AUDIT ===")

markers = (
    "/application1/",
    "/batch2/",
    "/workspace/",
)

found = 0
for p in sorted((release / "maxserve_cta_extension").rglob("*.py")):
    for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
        if any(m in line for m in markers):
            print(f"{p.name}:{n}: {line.strip()[:180]}")
            found += 1

print("ABSOLUTE PATH REFERENCES:", found)
print("VALIDATED BACKEND: PRESENT")
print("ACCEPTANCE REPORT:",
      "PRESENT" if (release / "CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json").is_file()
      else "MISSING")
print("ORIGINAL CODE: NOT MODIFIED")
print("READ-ONLY CHECK COMPLETE")
PY
