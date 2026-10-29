cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
from textwrap import dedent, indent
import ast

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
p = base / "native_batch2/cta_worker_adapter.py"
backend = base / "real_max_batch2_backend.py"

assert p.is_file(), f"STOP: Missing adapter: {p}"
assert backend.is_file(), f"STOP: Missing backend: {backend}"

src = p.read_text()
tree = ast.parse(src)

cls = next(
    (n for n in tree.body
     if isinstance(n, ast.ClassDef)
     and n.name == "CTAWorkerAdapter"),
    None
)
assert cls is not None, "STOP: Adapter class missing"

methods = {
    n.name for n in cls.body
    if isinstance(n, ast.FunctionDef)
}
assert "predict" in methods
assert "initialize" in methods
assert "predict_batch" not in methods, "STOP: Already implemented"

method = indent(dedent('''
def predict_batch(self, bodies):
    """Development-only genuine MAX batch-2 inference."""
    if not isinstance(bodies, (list, tuple)) or len(bodies) != 2:
        raise ValueError("Exactly two CTA JSON requests required")
    if not all(isinstance(x, dict) for x in bodies):
        raise TypeError("CTA requests must be JSON objects")

    import importlib.util
    import numpy as np
    import torch
    from pathlib import Path

    pipeline = self.initialize()

    # Preserve original data science implementation.
    original_preprocess = pipeline.preprocess
    original_base = pipeline.model_base
    original_atc = pipeline.model_atc

    # Obtain genuine model inputs using original CTA preprocessing.
    prepared = [original_preprocess(body) for body in bodies]

    if any(not isinstance(x, (tuple, list)) or len(x) != 7
           for x in prepared):
        raise RuntimeError("Unexpected CTA preprocessing contract")

    model_inputs = [x[0] for x in prepared]
    if any(not isinstance(x, dict) for x in model_inputs):
        raise TypeError("CTA model inputs must be dictionaries")

    locations = [
        Path("/batch2/real_max_batch2_backend.py"),
        Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
             "real_max_batch2_backend.py"),
    ]
    backend_file = next((x for x in locations if x.is_file()), None)
    if backend_file is None:
        raise RuntimeError("Real MAX batch backend not mounted")

    fn = getattr(self, "_real_max_batch_fn", None)
    if fn is None:
        spec = importlib.util.spec_from_file_location(
            "cta_real_max_batch2_dev", backend_file
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Cannot load MAX batch backend")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fn = module.infer_max_batch
        self._real_max_batch_fn = fn

    # ONE actual MAX execution for BOTH requests.
    output = np.asarray(
        fn(model_inputs[0], model_inputs[1]),
        dtype=np.float32
    )

    if output.shape != (2, 2048):
        raise RuntimeError(f"Invalid batch output: {output.shape}")
    if not np.isfinite(output).all():
        raise RuntimeError("Non-finite MAX batch output")

    responses = []

    class PrecomputedMAX:
        def __init__(self, values):
            self.tensor = torch.from_numpy(
                np.ascontiguousarray(values)
            )
            self.calls = 0

        def eval(self):
            return self

        def __call__(self, **kwargs):
            self.calls += 1
            if self.calls > 1:
                raise RuntimeError(
                    "Multiple CTA inference calls need explicit batching"
                )
            return self.tensor

    try:
        for i, body in enumerate(bodies):
            model = PrecomputedMAX(output[i:i+1])
            pipeline.model_base = model
            pipeline.model_atc = model

            response = pipeline.predict_raw(body)

            if model.calls != 1:
                raise RuntimeError(
                    "CTA request did not execute exactly one model inference"
                )
            if not isinstance(response, dict):
                raise TypeError("Original CTA response is not a dictionary")

            responses.append(response)

    finally:
        pipeline.model_base = original_base
        pipeline.model_atc = original_atc
        pipeline.preprocess = original_preprocess

    assert len(responses) == 2
    print(
        "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED",
        flush=True
    )
    return responses
''').strip("\n"), "    ") + "\n"

lines = src.splitlines(keepends=True)
updated = (
    "".join(lines[:cls.end_lineno])
    + "\n"
    + method
    + "".join(lines[cls.end_lineno:])
)

tree2 = ast.parse(updated)
cls2 = next(
    n for n in tree2.body
    if isinstance(n, ast.ClassDef)
    and n.name == "CTAWorkerAdapter"
)
assert sum(
    isinstance(n, ast.FunctionDef) and n.name == "predict_batch"
    for n in cls2.body
) == 1

backup = p.with_suffix(".py.before_batch2_backend.bak")
assert not backup.exists(), f"STOP: Backup exists: {backup}"

backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("DEV predict_batch: INSTALLED")
print("TWO REAL CTA REQUESTS: CONFIGURED")
print("ONE REAL MAX BATCH BACKEND CALL: WIRED")
print("ORIGINAL PREDICT_RAW: PRESERVED")
print("TWO RESPONSE CONTRACTS: CONFIGURED")
print("PYTHON SYNTAX: PASS")
print("REAL NATIVE BATCH E2E: NOT YET VALIDATED")
print("WORKING RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
print("FILE:", p)
PY
