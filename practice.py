
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import re

log = Path(
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_http_evidence/pzaas_clean_stage_http.log"
)

if not log.is_file():
    raise SystemExit("STOP: Clean-stage server log missing")

lines = log.read_text(errors="replace").splitlines()

print("=== CLEAN PZAAS WORKER ROOT-CAUSE INSPECTION ===")
print("TOTAL LOG LINES:", len(lines))

patterns = re.compile(
    r"Traceback|ModuleNotFoundError|ImportError|"
    r"FileNotFoundError|AttributeError|KeyError|"
    r"ValueError|TypeError|RuntimeError|"
    r"AssertionError|OSError|MemoryError|"
    r"worker died|worker exited|"
    r"PZAAS MODEL LOAD|PZAAS FACTORY|"
    r"PZAAS REAL MAX|PZAAS MAX BASE|"
    r"failed|exception|no such file",
    re.IGNORECASE
)

matches = [
    i for i, line in enumerate(lines)
    if patterns.search(line)
]

print("ERROR / LIFECYCLE MATCHES:", len(matches))

if matches:
    selected = matches[:8] + matches[-20:]
    indices = set()

    for i in selected:
        indices.update(
            range(
                max(0, i - 3),
                min(len(lines), i + 7)
            )
        )

    print("\n=== FAILURE CONTEXT ===")
    previous = -2

    for i in sorted(indices):
        if i > previous + 1:
            print("...")
        print(f"{i+1}: {lines[i][:350]}")
        previous = i

print("\n=== LAST 35 LOG LINES ===")

for i in range(max(0, len(lines)-35), len(lines)):
    print(f"{i+1}: {lines[i][:350]}")

print("\n=== NO FILES MODIFIED ===")
PY
