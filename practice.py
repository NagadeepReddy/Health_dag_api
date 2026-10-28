cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import re

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
files = [
    "cta_router.py",
    "cta_http_pipeline.py",
    "cta_queue_scheduler.py",
    "cta_scheduler.py",
    "cta_spawn_worker.py",
    "cta_native_e2e_test.py",
]

pattern = re.compile(
    r"response_worker|response_queue|response_queue_config|"
    r"request_id|requestId|RequestID|"
    r"engine_queue|queue\.get|queue\.put|"
    r"CTA HTTP FANOUT|CTA RECEIVER|"
    r"async def|def .*predict|def .*response|"
    r"schedule|wait_for|background_tasks|"
    r"ZmqConfig|ZmqPullSocket",
    re.I
)

for name in files:
    p = base / name
    print(f"\n========== {name} ==========")
    if not p.is_file():
        print("MISSING")
        continue
    lines = p.read_text().splitlines()
    matches = [i for i, line in enumerate(lines) if pattern.search(line)]
    positions = set()
    for i in matches:
        positions.update(range(max(0, i-3), min(len(lines), i+5)))
    for i in sorted(positions):
        print(f"{i+1:4}: {lines[i][:220]}")

log = Path("/application1/cta_native_corrected_1028.log")
print("\n========== RUNTIME EVENT SEQUENCE ==========")
if log.exists():
    keys = re.compile(
        r"CTA HTTP|CTA RECEIVER|CTA RESPONSE|CTA NATIVE|"
        r"CTA QUEUE|CTA ZMQ|HTTP STATUS|"
        r"Traceback|Exception|ERROR|Killed|"
        r"response_worker|request_id",
        re.I
    )
    found = [(i, s) for i, s in enumerate(log.read_text(errors="replace").splitlines(), 1) if keys.search(s)]
    for i, s in found[-65:]:
        print(f"{i}: {s[:250]}")
else:
    print("LOG MISSING")

print("\nDIAGNOSTIC COMPLETE — NO FILES MODIFIED")
PY
