python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py")
s = p.read_text()

start = '    sys.argv = ["max.entrypoints.pipelines", "serve", *sys.argv[1:]]'
end = '\nif __name__ == "__main__":'

assert s.count(start) == 1, "STOP: launcher structure changed"
assert s.count(end) == 1, "STOP: launcher ending changed"

replacement = '''
    from types import SimpleNamespace
    import uvicorn
    from max.serve import api_server
    from max.serve.config import Settings
    from max.interfaces import PipelineTask
    from bplan_native_serve_dev.bplan_http_pipeline import BPlanNativeHTTPPipeline

    api_server.TokenGeneratorPipeline = BPlanNativeHTTPPipeline

    config = SimpleNamespace(
        model_config=SimpleNamespace(
            model_name="bplan-v1.113",
            model_path="/workspace/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_model",
        ),
        lora_config=None,
        zmq_endpoint_base="ipc:///tmp/bplan-max-native",
    )

    serving = api_server.ServingTokenGeneratorSettings(
        model_factory=BPlanFactoryWrapper(),
        pipeline_config=config,
        tokenizer=None,
        pipeline_task=PipelineTask.TEXT_GENERATION,
    )

    app = api_server.fastapi_app(
        Settings(api_types=[api_server.APIType.KSERVE]),
        serving,
    )
    print("BPLAN BUILT-IN MAX SERVE: STARTING", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=18768)
'''

updated = s[:s.index(start)] + replacement + s[s.index(end):]
compile(updated, str(p), "exec")
p.write_text(updated)
py_compile.compile(str(p), doraise=True)

print("BPLAN NATIVE LAUNCHER: UPDATED")
print("BPLAN SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
