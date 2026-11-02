DEV=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

DEV="$DEV" python3 - <<'PY'
import os, ast
from pathlib import Path

dev = Path(os.environ["DEV"])
target = dev / "bplan_native_launcher.py"

for name in ("bplan_spawn_worker.py", "bplan_worker_registration.py",
             "bplan_architecture_registration.py"):
    assert (dev / name).is_file(), f"STOP: missing {name}"

assert not target.exists(), "STOP: launcher already exists"

code = '''"""BPLAN-only built-in Modular MAX Serve launcher."""

import inspect
import runpy
import sys


def main():
    from bplan_native_serve_dev.bplan_architecture_registration import (
        register_bplan_architecture,
    )
    from bplan_native_serve_dev.bplan_spawn_worker import BPlanFactoryWrapper

    register_bplan_architecture()

    from max.pipelines.lib import PIPELINE_REGISTRY
    original_factory = PIPELINE_REGISTRY.retrieve_factory

    def select_factory(config, *args, **kwargs):
        model_config = getattr(config, "model_config", None)
        model_path = str(getattr(model_config, "model_path", "")).rstrip("/")

        if model_path.endswith("/bplan_native_model"):
            print("BPLAN: native model factory selected", flush=True)
            return None, BPlanFactoryWrapper()

        return original_factory(config, *args, **kwargs)

    PIPELINE_REGISTRY.retrieve_factory = select_factory

    from max.serve.pipelines import model_worker

    original_spawn = model_worker.start_model_worker
    signature = inspect.signature(original_spawn)
    assert "model_factory" in signature.parameters

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def bplan_spawn(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.arguments["model_factory"] = BPlanFactoryWrapper(
            bound.arguments["model_factory"]
        )
        async with original_spawn(*bound.args, **bound.kwargs) as monitor:
            yield monitor

    model_worker.start_model_worker = bplan_spawn

    from max.serve import api_server
    if getattr(api_server, "start_model_worker", None) is original_spawn:
        api_server.start_model_worker = bplan_spawn

    print("BPLAN NATIVE MAX LAUNCHER: REGISTERED", flush=True)

    sys.argv = ["max.entrypoints.pipelines", "serve", *sys.argv[1:]]
    runpy.run_module("max.entrypoints.pipelines",
                     run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
'''

ast.parse(code)
target.write_text(code)

print("BPLAN NATIVE LAUNCHER: CREATED")
print("BPLAN SERVING REGISTRATION: PREPARED")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY

python3 -m py_compile "$DEV/bplan_native_launcher.py"
