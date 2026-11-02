python3 - <<'PY'
from pathlib import Path
import py_compile

src = Path("/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_http_pipeline.py")
dst = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_http_pipeline.py")

assert src.is_file(), f"Missing CTA reference: {src}"
assert dst.parent.is_dir(), f"Missing BPLAN directory: {dst}"
assert not dst.exists(), "STOP: BPLAN pipeline already exists; preserve it"

code = src.read_text()
code = code.replace("CTA", "BPLAN").replace("Cta", "BPlan").replace("cta", "bplan")

dst.write_text(code)
py_compile.compile(str(dst), doraise=True)

print("BPLAN ISOLATED HTTP PIPELINE: CREATED")
print("BPLAN PIPELINE SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
