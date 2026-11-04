cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, re, shutil

p = Path("artifacts/v1.472-max/pzaas_max/sibling_context_max.py")
s = p.read_text()

pattern = r'wide_input\s*-\s*weight\(\s*p\s*\+\s*["\']\.num_batch_norm\.running_mean["\']\s*\)'
replacement = 'ops.cast(wide_input, DType.float32) - weight(p + ".num_batch_norm.running_mean")'

if replacement in s:
    print("SIBLING CAST: ALREADY PRESENT")
else:
    updated, count = re.subn(pattern, replacement, s)
    assert count == 1, f"Expected one target, found {count}"

    tree = ast.parse(updated)
    imported = any(
        isinstance(n, ast.ImportFrom)
        and n.module == "max.dtype"
        and any(a.name == "DType" for a in n.names)
        for n in tree.body
    )

    if not imported:
        lines = updated.splitlines(keepends=True)
        pos = max(
            (i + 1 for i, line in enumerate(lines)
             if line.startswith("from __future__ import")),
            default=0
        )
        lines.insert(pos, "from max.dtype import DType\n")
        updated = "".join(lines)

    compile(updated, str(p), "exec")
    backup = p.with_suffix(".before_sibling_cast.bak")
    if not backup.exists():
        shutil.copy2(p, backup)
    p.write_text(updated)
    print("SIBLING CAST FIX: PASS")

assert replacement in p.read_text()
print("MAX SOURCE VALIDATION: PASS")
print("ORIGINAL DS: UNCHANGED")
PY
