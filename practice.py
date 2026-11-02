python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev/bplan_native_worker_adapter.py")
s = p.read_text()

target = "return backend(**kwargs)"

if "BPLAN REAL MAX EXECUTION PASS" in s:
    print("MAX EXECUTION LOGGING: ALREADY PRESENT")
elif s.count(target) == 1:
    lines = s.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if target in line:
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = (
                indent + 'print("BPLAN REAL MAX EXECUTION START", flush=True)\n'
                + indent + 'result = backend(**kwargs)\n'
                + indent + 'print("BPLAN REAL MAX EXECUTION PASS", flush=True)\n'
                + indent + 'return result\n'
            )
            break
    updated = "".join(lines)
    compile(updated, str(p), "exec")
    p.write_text(updated)
    print("MAX EXECUTION LOGGING: INSTALLED")
else:
    raise SystemExit("STOP: Backend call not uniquely identified; no changes made")

py_compile.compile(str(p), doraise=True)
print("BPLAN SYNTAX: PASS")
PY
