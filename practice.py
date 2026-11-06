
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path

base = Path("/application1/sajjna8")
models = {
    "CTA": (
        Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
        base / "max_shared_infra/isolated/cta_shared_wiring_v1",
        "cta_native_launcher.py",
    ),
    "BPLAN": (
        Path("/application1/BPLAN_MAX_TEAM_HANDOFF_20261102"),
        base / "max_shared_infra/isolated/bplan_shared_wiring_v1",
        "bplan_native_launcher.py",
    ),
}

print("=== CTA / BPLAN SHARED MODEL PACKAGE WIRING ===")

for name, (handoff, wiring, filename) in models.items():
    print(f"\n=== {name} ===")

    candidates = sorted(handoff.rglob(filename))
    print("ORIGINAL HANDOFF LAUNCHERS:", len(candidates))

    for path in candidates[:5]:
        print(" ", path)
        print(" IMPORT ROOT:", path.parent.parent)
        print(" MODULE:", path.parent.name + "." + path.stem)

    stage = wiring / filename
    print("SHARED WIRING LAUNCHER:", stage.is_file())

    if stage.is_file():
        print("SHARED LAUNCHER DEPENDENCIES:")
        for n, line in enumerate(
            stage.read_text(errors="replace").splitlines(), 1
        ):
            s = line.strip()
            if (
                s.startswith(("from ", "import "))
                or "port=" in s
                or "model_path=" in s
                or "PYTHONPATH" in s
            ):
                print(f"  {n}: {s[:160]}")

    print("ORIGINAL ARTIFACTS:",
          (handoff / "artifacts").is_dir())

print("\nORIGINAL HANDOFFS: UNCHANGED")
print("SHARED INFRASTRUCTURE: UNCHANGED")
print("CONTAINERS STARTED: NONE")
print("NEXT: CREATE RUNNABLE CTA/BPLAN SHARED PACKAGES")
PY
