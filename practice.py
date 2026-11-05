
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast
import shutil
import textwrap

native = Path(
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev"
)
spawn = native / "pzaas_spawn_worker.py"
worker = native / "pzaas_worker_adapter.py"
target = native / "pzaas_max_model_adapter.py"

print("=== PZAAS REAL MAX NATIVE BRIDGE ===")

assert spawn.is_file(), f"Missing: {spawn}"
assert worker.is_file(), f"Missing: {worker}"
assert not target.exists(), f"Existing bridge must be preserved: {target}"

old = spawn.read_text()
imports = {
    "from pzaas_max_model_adapter import PZAASMAXModel":
    "from pzaas_native_serve_dev.pzaas_max_model_adapter import PZAASMAXModel",
    "from pzaas_native_worker_adapter import PZAASNativeWorkerAdapter":
    "from pzaas_native_serve_dev.pzaas_max_model_adapter import PZAASNativeWorkerAdapter",
}
for before in imports:
    assert old.count(before) == 1, f"Unexpected factory import: {before}"

source = textwrap.dedent('''
    """PZAAS genuine MAX CPU bridge. Original DS source remains unchanged."""
    from contextvars import ContextVar
    from pathlib import Path
    import re
    import sys
    import numpy as np
    from .pzaas_worker_adapter import PZAASWorkerAdapter

    _input = ContextVar("pzaas_max_input", default=None)

    class PZAASMAXModel:
        def __init__(self):
            root = Path(__file__).resolve().parents[2]
            for path in (root, root / "pzaas_max"):
                if str(path) not in sys.path:
                    sys.path.insert(0, str(path))

            from max.driver import CPU
            from max.engine import InferenceSession
            from max.graph import DeviceRef
            from pzaas_max.grecbase_fusion_full_head_72_max import (
                build_grecbase_fusion_graph_order_correct,
            )
            from pzaas_max.pzaas_weight_loader import MANIFEST, load_weight
            from pzaas_max.validation.pzaas_forward_input_adapter import pack

            self.pack = pack
            graph = build_grecbase_fusion_graph_order_correct(
                DeviceRef.CPU()
            )

            registry = {}
            for weight in graph.weights:
                name = str(getattr(weight, "name", weight))
                fn_name = re.sub(
                    r"(\\.ptransformer\\.\\d+)\\.(?!fn\\.)",
                    r"\\1.fn.",
                    name,
                )
                candidates = (
                    name, name + ".weight",
                    fn_name, fn_name + ".weight",
                )
                matched = next(
                    (x for x in candidates if x in MANIFEST),
                    None,
                )
                if matched is None:
                    raise KeyError(f"Unbound MAX weight: {name}")
                registry[name] = np.ascontiguousarray(
                    load_weight(matched)
                )

            if len(registry) != 17:
                raise RuntimeError(
                    f"Expected 17 MAX weights, got {len(registry)}"
                )

            self.registry = registry
            self.session = InferenceSession(devices=[CPU()])
            self.model = self.session.load(
                graph, weights_registry=self.registry
            )
            print("PZAAS REAL MAX COMPILED: 17/17", flush=True)

        def __call__(self, model_in):
            import torch

            packed = self.pack(model_in)
            if len(packed) != 72:
                raise RuntimeError(
                    f"Expected 72 inputs, got {len(packed)}"
                )

            print("PZAAS REAL MAX EXECUTION: START", flush=True)
            outputs = self.model.execute(*packed)
            result = np.ascontiguousarray(
                outputs[0].to_numpy(), dtype=np.float32
            )

            if result.shape != (1, 2048):
                raise RuntimeError(
                    f"Unexpected MAX output: {result.shape}"
                )
            if not np.isfinite(result).all():
                raise RuntimeError("MAX output contains nonfinite values")

            print("PZAAS REAL MAX EXECUTION: PASS", flush=True)
            return torch.from_numpy(result)

    class PZAASNativeWorkerAdapter(PZAASWorkerAdapter):
        def __init__(self, pipeline_factory, max_factory):
            def attach_max(pipeline):
                real_max = max_factory()
                original_preprocess = pipeline.preprocess

                if not hasattr(pipeline.model_base, "forward"):
                    raise RuntimeError("Base-model forward not found")

                def capture(*args, **kwargs):
                    prepared = original_preprocess(*args, **kwargs)
                    if (
                        not isinstance(prepared, (tuple, list))
                        or not prepared
                        or not isinstance(prepared[0], dict)
                    ):
                        raise RuntimeError(
                            "Unexpected PZAAS preprocessing contract"
                        )
                    _input.set(prepared[0])
                    return prepared

                def max_forward(*args, **kwargs):
                    model_in = _input.get()
                    if model_in is None:
                        raise RuntimeError(
                            "Missing original preprocessed MAX input"
                        )
                    return real_max(model_in)

                pipeline.preprocess = capture
                pipeline.model_base.forward = max_forward
                pipeline._pzaas_real_max = real_max
                print("PZAAS MAX BASE HOOK: INSTALLED", flush=True)

            super().__init__(
                pipeline_factory=pipeline_factory,
                attach_max=attach_max,
            )

        def predict_batch(self, bodies):
            raise NotImplementedError(
                "PZAAS native batch-2 requires separate validation"
            )
''')

updated = old
for before, after in imports.items():
    updated = updated.replace(before, after)

ast.parse(source)
ast.parse(updated)

backup = spawn.with_suffix(".pre_max_bridge.bak")
if not backup.exists():
    shutil.copy2(spawn, backup)

target.write_text(source)
spawn.write_text(updated)

ast.parse(target.read_text())
ast.parse(spawn.read_text())

print("PZAAS MODEL BRIDGE: CREATED")
print("NATIVE FACTORY IMPORTS: CORRECTED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NATIVE MAX EXECUTION: REQUIRES RUNTIME TEST")
print("NEXT: NATIVE CONTAINER STARTUP AND REAL HTTP")
PY
