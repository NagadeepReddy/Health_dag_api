python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py")
s = p.read_text()
lines = s.splitlines(keepends=True)

if 'model_in["task_in"] = model_in["tasks_in"]' in s:
    print("TASK INPUT MAPPING ALREADY EXISTS")
else:
    matches = [
        i for i, line in enumerate(lines)
        if "result = np.asarray(infer_max_live(model_in)" in line
    ]
    if len(matches) != 1:
        print("INFERENCE CALL NOT FOUND — NO CHANGES")
    else:
        i = matches[0]
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        lines.insert(i,
            indent + 'if "task_in" not in model_in and "tasks_in" in model_in:\n'
            + indent + '    model_in["task_in"] = model_in["tasks_in"]\n'
        )
        updated = "".join(lines)
        compile(updated, str(p), "exec")

        backup = p.with_suffix(".py.before_task_mapping")
        if backup.exists():
            print("BACKUP EXISTS — NO CHANGES")
        else:
            backup.write_text(s)
            p.write_text(updated)
            print("MAX TASK INPUT MAPPING: READY")
            print("ORIGINAL DS CODE: UNCHANGED")
PY
