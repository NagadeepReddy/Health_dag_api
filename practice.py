python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/grecbase_fusion_batch2_draft.py")

if not p.is_file() or p.is_symlink():
    raise SystemExit("STOP: Isolated graph file unavailable")

s = p.read_text()
marker = "CTA_BATCH2_BRANCH_SHAPES"

if marker in s:
    print("TRACE ALREADY INSTALLED")
else:
    lines = s.splitlines(keepends=True)
    matches = [
        i for i, line in enumerate(lines)
        if "outs = ops.concat(" in line
        and "ops.reshape(x" in "".join(lines[i:i+8])
        and "seq" in "".join(lines[i:i+8])
    ]

    if len(matches) != 1:
        raise SystemExit(
            f"STOP: Expected one fusion call; found {len(matches)}"
        )

    i = matches[0]
    indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
    names = ("seq", "context", "search0", "search1",
             "task", "jet", "ihq", "sibling")

    trace = (
        indent + "print(" + repr(marker) +
        ", {n: str(v.type) for n, v in [" +
        ", ".join(f"({n!r}, {n})" for n in names) +
        "]}, flush=True)\n"
    )

    updated = "".join(lines[:i] + [trace] + lines[i:])
    ast.parse(updated)

    backup = p.with_name(p.name + ".before_branch_trace")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("ISOLATED SHAPE TRACE: INSTALLED")

print("SYNTAX: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("NEXT: Capture branch shapes during native graph build")
PY
