python3 - <<'PY'
from pathlib import Path
import shutil, ast

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max")
stage = root / "bplan_batch2_graph_dev"
name = "grecbase_fusion_full_head_72_max.py"

matches = [
    p for p in root.rglob(name)
    if stage not in p.parents and p.is_file()
]

print("MATCHING GRAPH SOURCES:", len(matches))
for p in matches:
    print("SOURCE:", p)

if len(matches) != 1:
    raise SystemExit("STOP: Need exactly one original graph source; nothing changed")

stage.mkdir(parents=True, exist_ok=True)
target = stage / name

if target.exists():
    print("PRESERVED EXISTING:", target)
else:
    shutil.copy2(matches[0], target)
    print("COPIED INTO ISOLATED STAGE:", target)

ast.parse(target.read_text(), filename=str(target))
print("BPLAN BATCH-2 MAIN GRAPH SYNTAX: PASS")
print("ORIGINAL SOURCE: UNCHANGED")
PY
