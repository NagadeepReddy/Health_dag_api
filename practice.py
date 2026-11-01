ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
from pathlib import Path
import os, json

root = Path(os.environ["ROOT"])
patterns = (
    "np.load(", "torch.load(", ".npy",
    "WDIR", "model_0_base.pt",
    "v1.168", "10438", "10819", "10727",
)

report = {}
for file in sorted((root / "bplan_max_dev").glob("*.py")):
    matches = [
        {"line": i, "code": line.strip()}
        for i, line in enumerate(file.read_text().splitlines(), 1)
        if any(p in line for p in patterns)
    ]
    if matches:
        report[file.name] = matches

out = root / "bplan_max_full_dependency_audit.json"
out.write_text(json.dumps(report, indent=2))

print("FULL DEPENDENCY AUDIT: SAVED")
print("FILES WITH REFERENCES:", len(report))
print("REFERENCES:", sum(map(len, report.values())))
print("REPORT:", out)
PY
