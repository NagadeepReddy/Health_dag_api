python3 - <<'PY'
from pathlib import Path
import re
import py_compile

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py")
s = p.read_text()

pattern = (
    r'(?m)^    sys\.argv = \["max\.entrypoints\.pipelines", "serve", \*sys\.argv\[1:\]\]\n'
    r'    runpy\.run_module\("max\.entrypoints\.pipelines", run_name="__main__", alter_sys=True\)'
)

replacement = '''    # BPLAN_NATIVE_HTTP_BOOTSTRAP_V1
    from types import SimpleNamespace
    import uvicorn
    from max.serve import api_server
    from max.serve.config import Settings
    from max.interfaces import PipelineTask
    from bplan_native_serve_dev.bplan_spawn_worker import BPlanFactoryWrapper

    serving = api_server.ServingTokenGeneratorSettings(
        model_factory=BPlanFactoryWrapper(),
        pipeline_config=SimpleNamespace(
            model_config=SimpleNamespace(
                model_name="bplan-v1.113",
                model_path="/workspace/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_model",
            ),
            lora_config=None,
            zmq_endpoint_base="ipc:///tmp/bplan-max-native",
        ),
        tokenizer=None,
        pipeline_task=PipelineTask.TEXT_GENERATION,
    )

    app = api_server.fastapi_app(
        Settings(api_types=[api_server.APIType.KSERVE]),
        serving,
    )
    print("BPLAN NATIVE MAX HTTP BOOTSTRAP: STARTING", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=18768)'''

if "BPLAN_NATIVE_HTTP_BOOTSTRAP_V1" not in s:
    s, n = re.subn(pattern, lambda _: replacement, s)
    assert n == 1, "STOP: launcher structure differs; no changes made"
    p.write_text(s)

py_compile.compile(str(p), doraise=True)
print("BPLAN NATIVE HTTP BOOTSTRAP: PREPARED")
print("BPLAN LAUNCHER SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
