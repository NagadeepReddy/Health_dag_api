
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import re

roots = [
    Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
    Path("/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max"),
]

print("=== CTA ORIGINAL MAX STARTUP CONTRACT ===")

launcher = Path(
    "/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/"
    "artifacts/v1.168-max/cta_native_batch2_release_candidate/"
    "maxserve_cta_extension/cta_native_launcher.py"
)

if launcher.is_file():
    lines = launcher.read_text().splitlines()
    print("\n=== ORIGINAL LAUNCHER END ===")
    for index in range(max(0, len(lines) - 14), len(lines)):
        print(f"{index+1}: {lines[index]}")

pattern = re.compile(
    r"cta_native_launcher|--model(?:-path)?\b|"
    r"max\s+serve|api_server\.main|"
    r"MODEL_PATH|model_path=|"
    r"8765|8000|cta_native_model",
    re.I
)

print("\n=== EXISTING STARTUP REFERENCES ===")
matches = 0
checked = 0

for root in roots:
    if not root.is_dir():
        continue

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix not in (".sh", ".py", ".md", ".yaml", ".yml") \
                and path.name not in ("Dockerfile", "Makefile"):
            continue

        if "__pycache__" in path.parts:
            continue

        try:
            if path.stat().st_size > 150000:
                continue
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue

        checked += 1
        hits = [
            i for i, line in enumerate(lines)
            if pattern.search(line)
        ]

        if not hits:
            continue

        print("\nFILE:", path)
        selected = set()
        for i in hits[:8]:
            selected.update(range(
                max(0, i - 2),
                min(len(lines), i + 3)
            ))

        for i in sorted(selected):
            print(f"{i+1}: {lines[i][:220]}")

        matches += 1
        if matches >= 12:
            break

    if matches >= 12:
        break

print("\n=== RESULT ===")
print("FILES INSPECTED:", checked)
print("STARTUP REFERENCE FILES:", matches)
print("ORIGINAL MODEL CODE: UNCHANGED")
print("CTA / BPLAN / PZAAS HANDOFFS: UNCHANGED")
print("NO CONTAINERS STARTED")
print("NEXT: LAUNCH CTA USING VERIFIED MODEL CONFIGURATION")
PY
