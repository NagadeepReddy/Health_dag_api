
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path

base = Path("/application1/sajjna8")
runner = base / "max_shared_infra/bin/run_max_model.sh"

candidates = [
    Path("/application1/BPLAN_MAX_TEAM_HANDOFF_20261102"),
    Path("/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102"),
    base / "rt-pzai-bplan-v1/artifacts/v1.113-max",
]

print("=== BPLAN SHARED MAX LIVE ADOPTION PREPARATION ===")

print("\nSHARED GENERIC RUNNER:")
print("PRESENT:", runner.is_file())

print("\nBPLAN PACKAGE CANDIDATES:")
for path in candidates:
    print(("FOUND: " if path.is_dir() else "NOT FOUND: ") + str(path))

launchers = []
for root in candidates:
    if root.is_dir():
        launchers.extend(root.rglob("bplan_native_launcher.py"))

print("\nBPLAN NATIVE LAUNCHERS:")
for path in launchers:
    print("FOUND:", path)

if not launchers:
    print("STOP: No BPLAN native launcher found")
    print("NO FILES MODIFIED")
    raise SystemExit(1)

for path in launchers[:3]:
    print("\nLAUNCHER:", path)
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if any(term in line for term in (
            "uvicorn.run",
            "fastapi_app",
            "register_bplan",
            "BPLANFactory",
            "Settings(",
            "port=",
            "model_path=",
        )):
            print(f"{i}: {line.strip()[:180]}")

print("\nSHARED RUNNER CONFIGURATION:")
if runner.is_file():
    for i, line in enumerate(runner.read_text().splitlines(), 1):
        if any(term in line for term in (
            "MODEL_PACKAGE",
            "MODEL_ENTRYPOINT",
            "HOST_PORT",
            "INTERNAL_PORT",
            "MAX_IMAGE",
        )):
            print(f"{i}: {line.strip()[:180]}")

print("\n=== RESULT ===")
print("BPLAN LAUNCHER DISCOVERY: PASS")
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
print("NO CONTAINERS STARTED")
print("NEXT: ISOLATED BPLAN SHARED MAX HTTP INTEGRATION")
PY
