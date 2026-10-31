python3 -B - <<'PY'
from pathlib import Path
import hashlib

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts")

pairs = [
    ("Original CTA", repo / "v1.168", clean / "v1.168"),
    ("Native MAX model", repo / "v1.168-max/cta_native_model",
     clean / "v1.168-max/cta_native_model"),
]

def inventory(root):
    result = {}
    for p in root.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
                    h.update(chunk)
            result[p.relative_to(root).as_posix()] = h.hexdigest()
    return result

all_pass = True
for label, source, target in pairs:
    if not source.is_dir() or not target.is_dir():
        print("FAIL:", label, "missing directory")
        all_pass = False
        continue
    original = inventory(source)
    copied = inventory(target)
    ok = original == copied
    print(f"{label}: {'PASS' if ok else 'FAIL'} | Files: {len(original)}")
    if not ok:
        for name in sorted(set(original) | set(copied)):
            if original.get(name) != copied.get(name):
                print("MISMATCH:", name)
        all_pass = False

print("ALL COPIED DEPENDENCIES MATCH:", all_pass)
print("ORIGINAL FILES: UNCHANGED")
PY
