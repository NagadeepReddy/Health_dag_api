DEV=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

DEV="$DEV" python3 - <<'PY'
import os, ast
from pathlib import Path

dev = Path(os.environ["DEV"])
model = dev / "bplan_pipeline_model.py"
registry = dev / "bplan_architecture_registration.py"

assert not model.exists() and not registry.exists(), "STOP: files already exist"

files = {
    model: '''
from max.pipelines.lib import PipelineModel

class BPlanMaxPipelineModel(PipelineModel):
    @classmethod
    def calculate_max_seq_len(cls, pipeline_config, huggingface_config):
        return 20

    @classmethod
    def infer_optimal_batch_size(cls, *args, **kwargs):
        return 1
''',
    registry: '''
from dataclasses import replace

def register_bplan_architecture():
    from max.pipelines.architectures.llama3.arch import llama_arch
    from max.pipelines.lib import PIPELINE_REGISTRY, SupportedEncoding
    from .bplan_pipeline_model import BPlanMaxPipelineModel

    arch = replace(
        llama_arch,
        name="BPlanMaxPipelineModel",
        pipeline_model=BPlanMaxPipelineModel,
        default_encoding=SupportedEncoding.float32,
        supported_encodings={
            SupportedEncoding.float32:
            llama_arch.supported_encodings[SupportedEncoding.bfloat16]
        },
    )
    PIPELINE_REGISTRY.register(arch, allow_override=True)
    return arch
'''
}

for path, code in files.items():
    ast.parse(code)
for path, code in files.items():
    path.write_text(code.strip() + "\n")

print("BPLAN NATIVE ARCHITECTURE: CREATED")
print("BPLAN REGISTRATION SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
