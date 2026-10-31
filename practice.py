python3 -B - <<'PY'
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
files = list((root / "artifacts/v1.168-max/cta_native_batch2_release_candidate").rglob("*.py"))
files.append(root / "batch2/real_max_batch2_backend.py")

terms = ("/workspace", "/batch2", "/application1")

print("=== RUNTIME PATH REFERENCE AUDIT ===")
count = 0
for p in sorted(files):
    if not p.is_file():
        print("MISSING:", p)
        continue
    for number, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
        if any(term in line for term in terms):
            print(f"{p.relative_to(root)}:{number}: {line.strip()[:180]}")
            count += 1

print("FILES SCANNED:", len(files))
print("PATH REFERENCES:", count)
print("READ-ONLY CHECK COMPLETE")
PY
