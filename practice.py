
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2_cached_overlay/cta_native_batch2_proven_server.py")

assert p.is_file() and not p.is_symlink(), "STOP: isolated launcher missing"

source = p.read_text()
marker = "_cta_cwd_fix.chdir('/workspace')"

if marker in source:
    print("ISOLATED CWD FIX: ALREADY INSTALLED")
else:
    tree = ast.parse(source)
    pos = 0

    for i, node in enumerate(tree.body):
        if i == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            pos = node.end_lineno
        elif isinstance(node, ast.ImportFrom) and node.module == "__future__":
            pos = node.end_lineno

    lines = source.splitlines(keepends=True)
    fix = (
        "\n# Isolated CTA MAX relative-weight path fix.\n"
        "import os as _cta_cwd_fix\n"
        "_cta_cwd_fix.chdir('/workspace')\n"
    )
    updated = "".join(lines[:pos]) + fix + "".join(lines[pos:])
    ast.parse(updated)

    backup = p.with_name(p.name + ".before_workspace_cwd_fix")
    assert not backup.exists(), "STOP: Backup already exists"
    shutil.copy2(p, backup)
    p.write_text(updated)

    print("ISOLATED CWD FIX: INSTALLED")
    print("BACKUP: PRESERVED")

print("SYNTAX: PASS")
print("TARGET WORKDIR: /workspace")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("ISOLATED RESTART: PENDING")
PY
