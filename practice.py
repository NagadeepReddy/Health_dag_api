cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py")
s = p.read_text()

old = 'cta_arch = replace(llama_arch, name="CTAMaxPipelineModel")'
new = '''from .cta_pipeline_model import CTAMaxPipelineModel
    cta_arch = replace(
        llama_arch,
        name="CTAMaxPipelineModel",
        pipeline_model=CTAMaxPipelineModel,
    )'''

assert old in s, "Expected registration line not found; no changes made"
p.write_text(s.replace(old, new, 1))

print("CTA MODEL REGISTRATION: UPDATED")
PY

python3 -m py_compile \
  artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py \
  && echo "CTA REGISTRATION SYNTAX: PASS"
