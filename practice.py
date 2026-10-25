cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py")
s = p.read_text()

old_import = "from max.pipelines.lib import PIPELINE_REGISTRY"
old_field = "pipeline_model=CTAMaxPipelineModel,"
new_field = old_field + "\n        default_encoding=SupportedEncoding.float32,"

if "default_encoding=SupportedEncoding.float32" in s:
    print("CTA FP32 DEFAULT: ALREADY SET")
else:
    assert s.count(old_import) == 1, "Unexpected import; no changes"
    assert s.count(old_field) == 1, "Unexpected model registration; no changes"

    updated = s.replace(
        old_import,
        "from max.pipelines.lib import PIPELINE_REGISTRY, SupportedEncoding",
        1
    ).replace(old_field, new_field, 1)

    compile(updated, str(p), "exec")

    backup = p.with_name(p.name + ".before_cta_fp32")
    assert not backup.exists(), "Backup exists; no changes"

    backup.write_text(s)
    p.write_text(updated)

    print("CTA FP32 DEFAULT: UPDATED")
    print("MAX-ONLY SYNTAX: PASS")
    print("BACKUP: SAVED")

print("ORIGINAL DS FILES: NOT MODIFIED")
PY
