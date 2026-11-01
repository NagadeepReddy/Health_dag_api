python3 - <<'PY'
from pathlib import Path
import re, json

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
dev = root / "bplan_max_dev"
manifest = json.loads((root / "max_weights/manifest.json").read_text())

report = {}
for p in sorted(dev.glob("*.py")):
    code = p.read_text()
    names = sorted(set(re.findall(r'WDIR\s*/\s*["\']([^"\']+\.npy)["\']', code)))
    if names:
        report[p.name] = {
            "weight_files": names,
            "matching_bplan_weights": [
                n for n in names if n[:-4] in manifest
            ],
            "needs_mapping": [
                n for n in names if n[:-4] not in manifest
            ]
        }

out = root / "bplan_max_weight_dependencies.json"
out.write_text(json.dumps(report, indent=2))

print("WEIGHT DEPENDENCY REPORT: SAVED")
print("SOURCE FILES:", len(report))
print("STATIC WEIGHT REFERENCES:", sum(len(x["weight_files"]) for x in report.values()))
print("REFERENCES NEEDING MAPPING:", sum(len(x["needs_mapping"]) for x in report.values()))
print("REPORT:", out)
PY
