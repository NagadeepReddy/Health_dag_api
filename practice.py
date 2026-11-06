
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import difflib
import re

base = Path("/application1/sajjna8")

paths = {
    "ORIGINAL CTA LAUNCHER":
        Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py"),
    "ISOLATED SHARED CTA LAUNCHER":
        base / "max_shared_infra/isolated/cta_shared_wiring_v1/cta_native_launcher.py",
}

print("=== CTA MAX STARTUP CONFIGURATION DIAGNOSIS ===")

content = {}
pattern = re.compile(
    r"model_config|model_path|model_name|model\s*=|"
    r"Settings|PipelineConfig|PipelineTask|SimpleNamespace|"
    r"fastapi_app|uvicorn|port=|8000|8765|"
    r"retrieve_factory|model_factory|config\s*=",
    re.I
)

for label, path in paths.items():
    print(f"\n=== {label} ===")
    print("PATH:", path)
    if not path.is_file():
        print("NOT FOUND")
        continue

    lines = path.read_text().splitlines()
    content[label] = lines
    print("TOTAL LINES:", len(lines))

    selected = set()
    for i, line in enumerate(lines):
        if pattern.search(line):
            selected.update(range(
                max(0, i - 3),
                min(len(lines), i + 5)
            ))

    for i in sorted(selected):
        print(f"{i+1:3}: {lines[i]}")

if len(content) == 2:
    a = content["ORIGINAL CTA LAUNCHER"]
    b = content["ISOLATED SHARED CTA LAUNCHER"]

    print("\n=== LAUNCHER DIFFERENCES ===")
    diff = list(difflib.unified_diff(
        a, b,
        fromfile="original",
        tofile="isolated",
        lineterm=""
    ))
    if diff:
        print("\n".join(diff[:120]))
        if len(diff) > 120:
            print("ADDITIONAL DIFFERENCES:", len(diff)-120)
    else:
        print("IDENTICAL")

print("\n=== RESULT ===")
print("ORIGINAL CTA HANDOFF: UNCHANGED")
print("ISOLATED CTA FILES: UNCHANGED")
print("NO CONTAINERS STARTED")
print("NEXT: CORRECT CTA MAX MODEL STARTUP CONFIGURATION")
PY
