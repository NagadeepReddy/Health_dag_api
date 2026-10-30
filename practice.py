python3 -B - <<'PY'
from pathlib import Path
import ast
import os
import shutil

root = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max"
)

working = root / "maxserve_cta_extension/cta_native_scheduler.py"
staged = (
    root / "cta_native_batch2_release_candidate/"
    "maxserve_cta_extension/cta_native_scheduler.py"
)

def get_method(tree):
    methods = [
        node
        for cls in tree.body
        if isinstance(cls, ast.ClassDef)
        for node in cls.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run_iteration"
    ]
    if len(methods) != 1:
        raise RuntimeError("Unexpected scheduler structure")
    return methods[0]

def has_response_send(method):
    for node in ast.walk(method):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if (
            isinstance(f, ast.Attribute)
            and f.attr in ("put_nowait", "put")
            and isinstance(f.value, ast.Attribute)
            and f.value.attr == "response_queue"
            and isinstance(f.value.value, ast.Name)
            and f.value.value.id == "self"
        ):
            return True
    return False

if not working.is_file() or not staged.is_file():
    raise SystemExit("STOP: Required scheduler source missing")

if working.is_symlink() or staged.is_symlink():
    raise SystemExit("STOP: Unexpected scheduler symlink")

original = working.read_text()
current = staged.read_text()

old_method = get_method(ast.parse(original))
new_method = get_method(ast.parse(current))

if not has_response_send(old_method):
    raise SystemExit("STOP: Working response contract not verified")

print("WORKING RESPONSE CONTRACT: VERIFIED")

if has_response_send(new_method):
    print("STAGED RESPONSE DISPATCH: ALREADY PRESENT")
else:
    returns = [
        n for n in new_method.body
        if isinstance(n, ast.Return)
    ]

    if len(returns) != 1 or new_method.body[-1] is not returns[0]:
        raise SystemExit("STOP: Unsafe insertion location")

    ret = returns[0]

    if not any(
        isinstance(n, ast.Name)
        and n.id == "responses"
        and isinstance(n.ctx, ast.Load)
        for n in ast.walk(new_method)
    ):
        raise SystemExit("STOP: Response dictionary not confirmed")

    lines = current.splitlines(keepends=True)
    indent = " " * ret.col_offset

    fix = (
        f"{indent}# CTA_BATCH2_RESPONSE_DISPATCH_FIX\n"
        f"{indent}if responses:\n"
        f"{indent}    self.response_queue.put_nowait(responses)\n"
        "\n"
    )

    lines.insert(ret.lineno - 1, fix)
    updated = "".join(lines)

    ast.parse(updated)
    compile(updated, str(staged), "exec")

    backup = staged.with_name(
        "cta_native_scheduler.py.before_response_fix.bak"
    )
    temp = staged.with_name(
        "cta_native_scheduler.py.response_fix.tmp"
    )

    if backup.exists() or temp.exists():
        raise SystemExit("STOP: Backup/temp already exists")

    shutil.copy2(staged, backup)

    try:
        with temp.open("x") as file:
            file.write(updated)
        os.replace(temp, staged)
    finally:
        if temp.exists():
            temp.unlink()

    print("ISOLATED RESPONSE FIX: INSTALLED")
    print("BACKUP:", backup)

verified = get_method(ast.parse(staged.read_text()))

if not has_response_send(verified):
    raise SystemExit("STOP: Response dispatch verification failed")

print("NATIVE RESPONSE QUEUE: PASS")
print("SYNTAX: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
