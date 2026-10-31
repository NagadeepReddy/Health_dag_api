python3 -B - <<'PY'
from pathlib import Path

base = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
ext = base / "cta_native_batch2_release_candidate/maxserve_cta_extension"

print("=== NATIVE SERVER STARTUP DEPENDENCIES ===")

names = [
    "cta_native_launcher.py",
    "cta_worker_adapter.py",
    "cta_http_pipeline.py",
    "cta_queue_compat.py",
    "cta_max_live_cta_pipeline_bridge.py",
]

for name in names:
    matches = list(base.rglob(name))
    print(f"{name}: {'FOUND' if matches else 'MISSING'}")
    for p in matches:
        print("  ", p.relative_to(base))

print("\n=== DYNAMIC IMPORT REFERENCES ===")
terms = [
    "cta_max_live_cta_pipeline_bridge",
    "importlib.import_module",
    "spec_from_file_location",
    "sitecustomize",
]

for p in sorted(ext.rglob("*.py")):
    for n, line in enumerate(p.read_text().splitlines(), 1):
        if any(term in line for term in terms):
            print(f"{p.name}:{n}: {line.strip()[:160]}")

print("\nORIGINAL FILES: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("READ-ONLY CHECK COMPLETE")
PY
