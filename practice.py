cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

marker = "def install_cta_spawn_entry():"
assert s.count(marker) == 1, "Unexpected file structure; no changes made"

replacement = '''def install_cta_spawn_entry():
    import sys
    from max.serve.pipelines import model_worker

    original = model_worker.start_model_worker
    if getattr(original, "_cta_wrapped", False):
        return

    signature = inspect.signature(original)
    assert "model_factory" in signature.parameters

    async def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.arguments["model_factory"] = CTAFactoryWrapper(
            bound.arguments["model_factory"]
        )
        return await original(*bound.args, **bound.kwargs)

    wrapped._cta_wrapped = True
    model_worker.start_model_worker = wrapped

    api = sys.modules.get("max.serve.pipelines.api_server")
    if api is not None and getattr(api, "start_model_worker", None) is original:
        api.start_model_worker = wrapped
'''

updated = s[:s.index(marker)] + replacement
compile(updated, str(p), "exec")
p.write_text(updated)

print("MODULE-LEVEL WORKER HOOK: CORRECTED")
print("SYNTAX: PASS")
PY
