cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil
import hashlib

src = Path("artifacts/v1.168-max/maxserve_cta_extension")
dst = Path("/application1/cta_max_native_release_candidate_20261028")

markers = (
    "CTA ROUTE QUEUE ID:",
    "CTA RECEIVER ENGINE ID:",
    "CTA RESPONSE ID MATCH:",
    "CTA RESPONSE SOCKET RECEIVED:",
    "CTA HTTP FANOUT:",
    "CTA QUEUE CONNECTION:",
    "CTA ACTUAL ENGINE QUEUE:",
)

assert src.is_dir() and dst.is_dir(), "STOP: Directory missing"

def digest(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*") if p.is_file()
    }

before = digest(src)
changes = {}

for p in sorted(dst.rglob("*.py")):
    original = p.read_text()
    tree = ast.parse(original)
    lines = original.splitlines(keepends=True)
    removals = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        if not isinstance(call.func, ast.Name) or call.func.id != "print":
            continue

        strings = [
            arg.value for arg in call.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        ]

        if any(marker in value for value in strings for marker in markers):
            removals.append((node.lineno, node.end_lineno))

    for start, end in sorted(removals, reverse=True):
        # Replace diagnostic logging with a harmless statement.
        # This preserves indentation and conditional-block validity.
        indentation = lines[start - 1][:
            len(lines[start - 1]) - len(lines[start - 1].lstrip())
        ]
        lines[start - 1:end] = [indentation + "pass\n"]

    updated = "".join(lines)
    ast.parse(updated)

    if updated != original:
        changes[p] = updated

assert digest(src) == before, "STOP: Working integration changed"
assert shutil.disk_usage("/application1").free > 1024**3, \
    "STOP: Disk space insufficient"

for p in changes:
    backup = p.with_name(p.name + ".before_log_cleanup.bak")
    assert not backup.exists(), f"STOP: Backup exists: {backup}"

for p, updated in changes.items():
    backup = p.with_name(p.name + ".before_log_cleanup.bak")
    backup.write_bytes(p.read_bytes())
    p.write_text(updated)

assert digest(src) == before, "STOP: Working source modified"

for p in dst.rglob("*.py"):
    ast.parse(p.read_text())

print("RELEASE CANDIDATE DIAGNOSTIC CLEANUP: PASS")
print("FILES CLEANED:", len(changes))
print("SYNTAX: PASS")
print("WORKING HTTP 200 SOURCE: UNCHANGED")
print("QUEUE BRIDGE AND SCHEDULER: PRESERVED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
print("RELEASE CANDIDATE RUNTIME: NOT YET VALIDATED")
PY
