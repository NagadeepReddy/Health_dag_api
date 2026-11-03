python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
folders = [
    root / "artifacts/v1.113/core-artifact",
    root / "artifacts/v1.113-max/maxserve_bplan_extension",
]
terms = ("ctalist", "serviceWidget", "propositionList",
         "postprocess(", "process_scores(", "predict_raw(")

for folder in folders:
    print(f"\n=== {folder} ===")
    for file in sorted(folder.rglob("*.py")):
        if "__pycache__" in file.parts:
            continue
        lines = file.read_text(errors="replace").splitlines()
        matches = [
            i for i, line in enumerate(lines)
            if any(t.lower() in line.lower() for t in terms)
        ]
        if not matches:
            continue
        print(f"\nFILE: {file.relative_to(root)}")
        for i in matches[:18]:
            print(f"{i+1}: {lines[i].strip()[:220]}")
        if len(matches) > 18:
            print(f"... {len(matches)-18} more matches")
print("\nREAD-ONLY POSTPROCESSING INSPECTION COMPLETE")
PY
