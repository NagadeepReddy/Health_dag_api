python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
core = root / "artifacts/v1.113/core-artifact"
ext = root / "artifacts/v1.113-max/maxserve_bplan_extension"

print("=== EXISTING PARITY / VALIDATION SCRIPTS ===")
for base in (core, ext):
    for p in sorted(base.rglob("*.py")):
        if any(x in p.name.lower() for x in (
            "parity", "compare", "baseline", "validate"
        )):
            print(p.relative_to(root))

print("\n=== ORIGINAL PYTORCH PIPELINE ===")
for name in ("pipeline.py", "model.py", "models.py"):
    p = core / name
    if not p.exists():
        continue

    lines = p.read_text(errors="replace").splitlines()
    keys = (
        "class ", "def load(", "def predict_raw(",
        "def preprocess(", "def inference(",
        "def postprocess(", "def predict("
    )

    print(f"\n--- {name} ---")
    for i, line in enumerate(lines):
        if line.lstrip().startswith(keys):
            print(f"{i+1}: {line[:150]}")

print("\n=== MAX PIPELINE FACTORY ===")
for p in sorted(ext.rglob("*.py")):
    lines = p.read_text(errors="replace").splitlines()
    hits = [
        i for i, line in enumerate(lines)
        if any(x in line for x in (
            "pipeline_factory", "max_factory",
            "BPlanNativeWorkerAdapter(",
            "BPlanMAXModel("
        ))
    ]
    if hits:
        print(f"\n--- {p.relative_to(root)} ---")
        for i in hits[:12]:
            for j in range(max(0, i-2), min(len(lines), i+4)):
                print(f"{j+1}: {lines[j][:160]}")
            print("---")
PY
