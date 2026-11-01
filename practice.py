ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
from pathlib import Path
import json, os

root = Path(os.environ["ROOT"])
cta = Path("/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_max")
manifest = json.loads((root / "max_weights/manifest.json").read_text())

folders = [
    "grecbase_integration_weights",
    "main_context_weights",
    "sibling_context_weights",
    "grecbase_aux_weights"
]

report = {}
for folder in folders:
    directory = cta / folder
    for p in sorted(directory.glob("*.npy")):
        name = p.stem
        candidates = [k for k in manifest if
                      k == name or
                      k.endswith("." + name) or
                      name.replace(".g", ".weight") == k]
        report[f"{folder}/{p.name}"] = candidates

out = root / "bplan_helper_weight_mapping.json"
out.write_text(json.dumps(report, indent=2))

matched = sum(bool(v) for v in report.values())
print("BPLAN HELPER WEIGHT MAPPING: SAVED")
print("CTA FORMAT FILES:", len(report))
print("NAME MATCH CANDIDATES:", matched)
print("UNRESOLVED:", len(report) - matched)
print("REPORT:", out)
for name, candidates in report.items():
    if not candidates:
        print("NEEDS MAPPING:", name)
PY
