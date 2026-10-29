python3 -S -B - <<'PY'
from pathlib import Path
import re

p = Path("/application1/cta_kserve_final_test.log")
if not p.is_file():
    raise SystemExit("STOP: Live-test log missing")

lines = p.read_text(errors="replace").splitlines()

patterns = re.compile(
    r"CTA|factory|worker|scheduler|queue|"
    r"predict_raw|inference|model loaded|"
    r"request_id|response|timeout|"
    r"Traceback|Error|Exception|Killed|OOM",
    re.I
)

matches = [
    (i, line)
    for i, line in enumerate(lines, 1)
    if patterns.search(line)
    and "telemetry.modular.com" not in line
    and "opentelemetry/" not in line
    and "site-packages/requests/" not in line
]

print("=== REAL NATIVE REQUEST LIFECYCLE ===")
print("TOTAL MATCHES:", len(matches))

selected = matches[:65] + matches[-65:]
seen = set()

for number, line in selected:
    if number in seen:
        continue
    seen.add(number)
    print(f"{number}: {line[:400]}")

print("=== CHECK COMPLETE — NO FILES MODIFIED ===")
PY
