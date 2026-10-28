cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/grecbase_fusion_full_head_72_max.py"
)

src = p.read_text()
tree = ast.parse(src)
lines = src.splitlines(keepends=True)

matches = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id == "outs"
               for t in node.targets):
            segment = ast.get_source_segment(src, node) or ""
            if "ops.reshape" in segment and "ops.concat" in segment:
                matches.append(node)

assert len(matches) == 1, "STOP: Fusion assignment differs"

node = matches[0]
indent = lines[node.lineno - 1][:node.col_offset]
marker = "CTA_BATCH_BRANCH_SHAPES"

if marker in src:
    print("BRANCH DIAGNOSTIC: ALREADY INSTALLED")
else:
    names = (
        "seq", "context", "search0", "search1",
        "jet", "ihq", "sibling", "task"
    )

    diagnostic = (
        indent + "# " + marker + "\n"
        + "".join(
            indent
            + f'print("CTA BRANCH {name}:", {name}, flush=True)\n'
            for name in names
        )
    )

    updated = (
        "".join(lines[:node.lineno - 1])
        + diagnostic
        + "".join(lines[node.lineno - 1:])
    )

    ast.parse(updated)

    backup = p.with_name(p.name + ".before_branch_diagnostic.bak")
    assert not backup.exists(), "STOP: Backup already exists"

    backup.write_bytes(p.read_bytes())
    p.write_text(updated)
    print("BRANCH DIAGNOSTIC: INSTALLED")

print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("WORKING MODEL: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
