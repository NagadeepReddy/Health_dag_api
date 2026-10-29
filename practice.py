python3 - <<'PY'
from pathlib import Path

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
stage = dev / "native_batch2_live_stage"

files = [
    "cta_router.py",
    "cta_native_launcher.py",
]

terms = (
    "register_cta_routes",
    "APIType",
    "KSERVE",
    "cta/predict",
    "cta/infer",
    "add_api_route",
    "include_router",
    "run_module",
    "sys.argv",
    "--api-type",
    "ROUTES",
)

for name in files:
    path = stage / name
    assert path.is_file(), f"STOP: Missing {path}"

    lines = path.read_text().splitlines()
    selected = set()

    for i, line in enumerate(lines):
        if any(term.lower() in line.lower() for term in terms):
            selected.update(range(
                max(0, i - 3),
                min(len(lines), i + 5)
            ))

    print(f"\n=== {name} ===")
    for i in sorted(selected):
        print(f"{i+1}: {lines[i]}")

log = dev / "native_batch2_live_http_test.log"

print("\n=== LAST NATIVE HTTP RESULT ===")
assert log.is_file(), "STOP: Previous HTTP log missing"

for line in log.read_text(errors="replace").splitlines():
    if any(term in line for term in (
        "HTTP READY",
        "HTTP ROUTE",
        "HTTP RESPONSE",
        "404",
        "Traceback",
        "Server ready",
    )):
        print(line[:250])

print("\nREAD-ONLY ROUTE CHECK COMPLETE")
print("NO FILES MODIFIED")
print("NO SERVER STARTED")
PY
