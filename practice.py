cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -B - <<'PY'
import ast
from pathlib import Path
from types import SimpleNamespace

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
tree = ast.parse(p.read_text())

fn = next(n for n in ast.walk(tree)
          if isinstance(n, ast.FunctionDef)
          and n.name == "cta_retrieve_factory")

class DummyFactory:
    def __init__(self, value):
        pass

scope = {
    "CTAFactoryWrapper": DummyFactory,
    "original_retrieve_factory": lambda *a, **k: ("ORIGINAL", None),
}

exec(compile(ast.Module(body=[fn], type_ignores=[]), str(p), "exec"), scope)

for path in ("/workspace/artifacts/v1.168/core-artifact",
             "/workspace/cta_native_model"):
    cfg = SimpleNamespace(model_config=SimpleNamespace(model_path=path))
    result = scope["cta_retrieve_factory"](cfg)
    assert isinstance(result, tuple) and len(result) == 2
    assert result[0] is None and isinstance(result[1], DummyFactory)
    print("CTA FACTORY SELECTION: PASS", path)

cfg = SimpleNamespace(model_config=SimpleNamespace(model_path="/other/model"))
assert scope["cta_retrieve_factory"](cfg) == ("ORIGINAL", None)
print("NON-CTA FALLBACK: PASS")
PY
