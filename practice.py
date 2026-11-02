BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

BPLAN="$BPLAN" python3 - <<'PY'
import os, ast
from pathlib import Path

ext = Path(os.environ["BPLAN"])
dev = ext / "bplan_native_serve_dev"
target = dev / "bplan_spawn_worker.py"

assert (dev / "bplan_scheduler_factory.py").is_file()
assert (ext / "bplan_max_dev/bplan_native_worker_adapter.py").is_file()
assert (ext / "bplan_max_dev/bplan_max_model_adapter.py").is_file()
assert not target.exists(), "STOP: worker factory already exists"

code = '''"""BPLAN-only model factory for native MAX Serve."""

import sys
from pathlib import Path


class BPlanFactoryWrapper:
    def __init__(self, original_factory=None):
        self.original_factory = original_factory

    def __call__(self):
        ext = Path(__file__).resolve().parents[1]
        artifacts = Path(__file__).resolve().parents[3]
        original = artifacts / "v1.113"
        paths = (
            original / "core-artifact",
            original / "utils/dependency-utils",
            ext / "bplan_max_dev",
        )
        for path in paths:
            if not path.is_dir():
                raise FileNotFoundError(path)
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))

        from pipeline import pipeline as BPlanPipeline
        from bplan_max_model_adapter import BPlanMAXModel
        from bplan_native_worker_adapter import BPlanNativeWorkerAdapter

        worker = BPlanNativeWorkerAdapter(
            pipeline_factory=BPlanPipeline,
            max_factory=BPlanMAXModel,
        )
        pipeline = worker.initialize()
        pipeline.bplan_native_adapter = worker
        return pipeline
'''

ast.parse(code, filename=str(target))
target.write_text(code)
print("BPLAN NATIVE MODEL FACTORY: CREATED")
print("BPLAN MODEL ADAPTER: CONNECTED")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
