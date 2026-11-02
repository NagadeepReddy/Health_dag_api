CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension
BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

CTA="$CTA" BPLAN="$BPLAN" python3 - <<'PY'
import os, ast
from pathlib import Path

source = Path(os.environ["CTA"])
target = Path(os.environ["BPLAN"]) / "bplan_native_serve_dev"

files = {
    "cta_context.py": "bplan_context.py",
    "cta_native_scheduler.py": "bplan_native_scheduler.py",
}

assert all((source / f).is_file() for f in files), "STOP: source file missing"
assert not target.exists(), "STOP: BPLAN native directory already exists"

prepared = {}
for old, new in files.items():
    code = (source / old).read_text()
    code = code.replace("CTA", "BPlan").replace("cta", "bplan")
    if new == "bplan_native_scheduler.py":
        code = code.replace(
            "max_items_per_iteration=2",
            "max_items_per_iteration=1"
        )
    ast.parse(code, filename=new)
    prepared[new] = code

target.mkdir(parents=True)
(target / "__init__.py").write_text("")

for name, code in prepared.items():
    (target / name).write_text(code)
    print("CREATED:", name)

print("BPLAN ISOLATED SCHEDULER: CREATED")
print("NATIVE SINGLE-REQUEST CAPACITY: 1")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
