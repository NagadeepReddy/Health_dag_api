python3 -B - <<'PY'
from pathlib import Path
import ast
import hashlib
import re

base = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
backend = base / "real_max_batch2_backend.py"
pkg = base / "cta_max"

old = "/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
helper_src = Path(old) / "run_batch2_contract.py"
helper_dst = pkg / "run_batch2_contract.py"

assert backend.is_file() and not backend.is_symlink()
assert pkg.is_dir() and not pkg.is_symlink()
assert helper_src.is_file() and not helper_src.is_symlink()
assert not helper_dst.is_symlink()

original = backend.read_text()
helper = helper_src.read_bytes()
ast.parse(helper.decode(), filename=str(helper_src))

replacement = 'str(Path(__file__).resolve().parent / "cta_max")'

def replace_literal(text, value, expected):
    pattern = re.compile(
        r"""(["'])""" + re.escape(value) + r"""\1"""
    )
    updated, count = pattern.subn(lambda m: replacement, text)
    assert count == expected, (
        f"STOP: expected {expected} references to {value}, found {count}"
    )
    return updated

updated = replace_literal(original, old, 4)
updated = replace_literal(updated, "/batch2/cta_max", 2)

# Make Path available before its first use.
assert "from __future__ import" not in original
updated = "from pathlib import Path\n" + updated

ast.parse(updated, filename=str(backend))
assert old not in updated
assert "/batch2/cta_max" not in updated

if helper_dst.exists():
    assert helper_dst.is_file()
    assert helper_dst.read_bytes() == helper, "STOP: helper differs"
    print("HELPER ALREADY IDENTICAL")
else:
    helper_dst.write_bytes(helper)
    print("REQUIRED HELPER COPIED")

assert helper_dst.read_bytes() == helper

backend.write_text(updated)
assert backend.read_text() == updated

print("OLD DEVELOPMENT REFERENCES FIXED: 4")
print("OLD BATCH2 REFERENCES FIXED: 2")
print("BACKEND SYNTAX: PASS")
print("HELPER SHA256:", hashlib.sha256(helper).hexdigest())
print("ORIGINAL FILES: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("CLEAN PATH CORRECTION: PASS")
PY
