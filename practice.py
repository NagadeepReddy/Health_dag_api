cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py")
assert not p.exists(), "STOP: Bridge already exists"

code = '''
import numpy as np
import torch

from cta_max.run_live_max_inference import infer_max_live

class MaxCTAInference:
    def eval(self):
        return self

    def __call__(self, **model_in):
        result = np.asarray(infer_max_live(model_in), dtype=np.float32)
        assert result.shape == (1, 2048), "Unexpected MAX output"
        assert np.isfinite(result).all(), "Non-finite output"
        return torch.from_numpy(np.ascontiguousarray(result))

def attach_max(pipeline):
    pipeline.model_atc = MaxCTAInference()
    return pipeline
'''

ast.parse(code)
p.write_text(code)

print("MAX PIPELINE BRIDGE: CREATED")
print("ORIGINAL PREPROCESSING: UNCHANGED")
print("ORIGINAL SCORING/POSTPROCESSING: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("PYTHON SYNTAX: PASS")
print("JSON END-TO-END: NOT YET TESTED")
PY
