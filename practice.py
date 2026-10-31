python3 -B - <<'PY'
from pathlib import Path
import ast, hashlib

base = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
pkg = base / "cta_max"
backend = base / "real_max_batch2_backend.py"

old_dir = "/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
source = Path(old_dir) / "run_batch2_contract.py"
target = pkg / "run_batch2_contract.py"

assert base.is_dir() and pkg.is_dir()
assert backend.is_file() and not backend.is_symlink()
assert source.is_file() and not source.is_symlink()
assert not target.is_symlink()

original = backend.read_text()
assert original.count(f'"{old_dir}"') == 4, "STOP: unexpected old-path occurrences"
assert original.count('"/batch2/cta_max"') == 2, "STOP: unexpected fallback occurrences"

helper = source.read_bytes()
ast.parse(helper.decode(), filename=str(source))

replacement = 'str(Path(__file__).resolve().parent / "cta_max")'
updated = original.replace(f'"{old_dir}"', replacement)
updated = updated.replace('"/batch2/cta_max"', replacement)

# Path must be available before the first replacement executes.
updated = "from pathlib import Path\n" + updated
ast.parse(updated, filename=str(backend))

if target.exists():
    assert target.is_file() and target.read_bytes() == helper, "STOP: existing helper differs"
    print("BATCH HELPER ALREADY IDENTICAL")
else:
    with target.open("xb") as f:
        f.write(helper)
    print("BATCH HELPER COPIED")

assert target.read_bytes() == helper
backend.write_text(updated)
assert backend.read_text() == updated
assert old_dir not in updated and "/batch2/cta_max" not in updated

print("CLEAN BACKEND PATHS UPDATED: 6")
print("BACKEND SYNTAX: PASS")
print("HELPER SHA256:", hashlib.sha256(helper).hexdigest())
print("ORIGINAL FILES: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
