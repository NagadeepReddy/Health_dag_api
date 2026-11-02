DEV=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

DEV="$DEV" python3 - <<'PY'
import os
from pathlib import Path

target = Path(os.environ["DEV"]) / "bplan_native_worker_adapter.py"
assert not target.exists(), "STOP: adapter already exists; do not overwrite"
assert (target.parent / "bplan_max_model_adapter.py").is_file()

target.write_text('''"""BPLAN native MAX Serve worker adapter. No DS changes."""

import gc


class BPlanNativeWorkerAdapter:
    def __init__(self, pipeline_factory, max_factory):
        self.pipeline_factory = pipeline_factory
        self.max_factory = max_factory
        self.pipeline = None
        self.backend = None
        self.max_calls = 0

    def initialize(self):
        if self.pipeline is None:
            pipeline = self.pipeline_factory()
            pipeline.load()

            assert pipeline.loaded
            pipeline.bplan_model = None
            pipeline.base_model = None
            gc.collect()

            backend = self.max_factory()

            class MAXProxy:
                def __call__(_, **kwargs):
                    self.max_calls += 1
                    return backend(**kwargs)

            pipeline.bplan_model = MAXProxy()
            self.backend = backend
            self.pipeline = pipeline

        return self.pipeline

    def predict(self, body):
        if not isinstance(body, dict):
            raise TypeError("BPLAN request must be a JSON object")

        pipeline = self.initialize()
        return pipeline.predict_raw(body)
''')

print("BPLAN NATIVE WORKER ADAPTER: CREATED")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY

python3 -m py_compile "$DEV/bplan_native_worker_adapter.py"
