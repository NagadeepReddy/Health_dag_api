python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py")
s = p.read_text()

lines = s.splitlines(keepends=True)
matches = [
    i for i, line in enumerate(lines)
    if "result = np.asarray(infer_max_live(model_in)" in line
]

if "MAX INFERENCE EXECUTED:" in s:
    print("MARKER ALREADY EXISTS")
elif len(matches) != 1:
    print("EXACT INFERENCE CALL NOT FOUND — no changes made")
else:
    i = matches[0]
    indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]

    lines.insert(
        i + 1,
        indent + 'print("MAX INFERENCE EXECUTED:", result.shape, flush=True)\n'
    )

    updated = "".join(lines)
    compile(updated, str(p), "exec")

    backup = p.with_suffix(".py.before_marker")
    if backup.exists():
        print("BACKUP ALREADY EXISTS — no changes made")
    else:
        backup.write_text(s)
        p.write_text(updated)
        print("MAX EXECUTION MARKER: READY")
        print("ORIGINAL DS CODE: UNCHANGED")
PY
