python3 - <<'PY'
import json
import subprocess
from pathlib import Path

base = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples")
expected_file = base / "test_sample_myplan_bundle_output.json"
actual_file = Path("/tmp/bplan_myplan_trace.json")

print("=== BUSINESS RESPONSE DIFFERENCES ===")
if not expected_file.is_file() or not actual_file.is_file():
    print("STOP: Response files missing")
else:
    def load(p):
        obj = json.loads(p.read_text())
        data = obj.get("jsonData", obj)
        return json.loads(data) if isinstance(data, str) else data

    expected = load(expected_file)
    actual = load(actual_file)
    differences = []

    def compare(a, b, path="$"):
        if type(a) is not type(b):
            differences.append((path, repr(a)[:100], repr(b)[:100]))
        elif isinstance(a, dict):
            for k in sorted(a.keys() | b.keys()):
                if k not in a or k not in b:
                    differences.append((path+"."+str(k),
                                        repr(a.get(k, "<MISSING>"))[:100],
                                        repr(b.get(k, "<MISSING>"))[:100]))
                else:
                    compare(a[k], b[k], path+"."+str(k))
        elif isinstance(a, list):
            if len(a) != len(b):
                differences.append((path+".length", len(a), len(b)))
            for i, (x,y) in enumerate(zip(a,b)):
                compare(x,y,f"{path}[{i}]")
        elif a != b:
            differences.append((path,repr(a)[:100],repr(b)[:100]))

    compare(expected,actual)
    print("TOTAL DIFFERENCES:",len(differences))
    for path,e,a in differences[:12]:
        print("FIELD:",path)
        print(" EXPECTED:",e)
        print(" ACTUAL:  ",a)

print("\n=== MAX EXECUTION EVENTS ===")
cmd = [
    "podman","--root","/application1/podman/storage",
    "--runroot","/run/containers/storage",
    "logs","--tail","1200","bplan-debug"
]
r = subprocess.run(cmd,capture_output=True,text=True)
lines = (r.stdout+"\n"+r.stderr).splitlines()

markers = (
    "BPLAN REAL MAX EXECUTION",
    "BPLAN MAX BACKEND",
    "BPLAN RESPONSE ID MATCH",
    "BPLAN TRACE:",
    "BPLAN RESPONSE SOCKET"
)
for line in lines:
    if any(m in line for m in markers):
        print(line[:240])

print("\n=== NON-TELEMETRY ERRORS ===")
errors = [
    line[:240] for line in lines
    if any(x in line for x in
           ("RuntimeError:", "ValueError:", "AssertionError:",
            "AttributeError:", "BPLAN PREDICT", "MAX execution failed"))
    and "telemetry.modular.com" not in line
]
for line in errors[-15:]:
    print(line)
PY
