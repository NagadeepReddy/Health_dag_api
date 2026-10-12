python - <<'PY'
from pathlib import Path
import ast

b = Path("artifacts/v1.168-max/cta_max")
src = b / "context_head_full.py"
deep = b / "context_head_deep.py"
dst = b / "context_head_base_max.py"

assert src.is_file() and deep.is_file()
assert not dst.exists(), "STOP: adapter already exists"

tree = ast.parse(deep.read_text())
cls = next(n for n in tree.body
           if isinstance(n, ast.ClassDef)
           and n.name == "ContextHeadDeepMAX")
dims = next(ast.literal_eval(n.value)
            for n in cls.body
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "DEEP_DIMS"
                    for t in n.targets))

assert len(dims) > 11, "STOP: extraction index unavailable"

code = '''
from context_head_full import ContextHeadFullMAX
from max.graph import TensorValue, ops

class ContextHeadBaseMAX(ContextHeadFullMAX):
    def __call__(
        self,
        deep_in: list[TensorValue],
        wide_in: TensorValue,
        bn_weight: TensorValue,
        bn_bias: TensorValue,
        running_mean: TensorValue,
        running_var: TensorValue,
    ):
        ctx_out = super().__call__(
            deep_in, wide_in,
            bn_weight, bn_bias,
            running_mean, running_var,
        )
        extracted = self.deep.deep_embedding[11](deep_in[11])
        extracted = ops.squeeze(extracted, axis=1)
        return ctx_out, extracted
'''

ast.parse(code)
dst.write_text(code)

print("BASE CONTEXTHEAD ADAPTER CREATED — SYNTAX OK")
print("EXTRACTED FEATURE INDEX: 11")
print("ORIGINAL CONTEXTHEAD, TRANSFORMER AND DS CODE UNCHANGED")
PY
