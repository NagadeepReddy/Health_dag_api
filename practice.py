python3 -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
folders = [
    root / "batch2",
    root / "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension",
    root / "artifacts/v1.168-max/cta_native_model",
]

files = sorted(set(
    p for folder in folders if folder.is_dir()
    for p in folder.rglob("*.py")
))

errors = []
old_paths = []

for p in files:
    source = p.read_text(errors="replace")
    try:
        ast.parse(source, filename=str(p))
    except SyntaxError as e:
        errors.append(f"{p.relative_to(root)}:{e.lineno}: {e.msg}")

    for n, line in enumerate(source.splitlines(), 1):
        if "/application1/" in line:
            old_paths.append(f"{p.relative_to(root)}:{n}: {line.strip()[:150]}")

print("PYTHON FILES CHECKED:", len(files))
print("SYNTAX:", "PASS" if not errors else "FAIL")
for e in errors:
    print("ERROR:", e)

print("ABSOLUTE VM PATH REFERENCES:", len(old_paths))
for item in old_paths:
    print(item)

print("READ-ONLY CHECK COMPLETE")
PY
